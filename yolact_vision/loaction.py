import cv2
import numpy as np
import torch
from data import set_cfg, cfg, mask_type, MEANS, STD, activation_func, COLORS
from utils.augmentations import Resize
from utils import timer
from layers.box_utils import crop, sanitize_coordinates
from utils.augmentations import FastBaseTransform
from yolact import Yolact
from pycocotools import coco
import torch.nn.functional as F
import os, sys
import datetime
class YolactRealtimeDetection:
    def __init__(self, model_path='weights/yolact_base_99_1000.pth'):
        set_cfg('yolact_base_config')
        self.model = Yolact()
        self.model.load_weights(model_path)
        self.model.cuda().eval()
        self.model.detect.use_fast_nms = True

    
    def undo_image_transformation(self,img, w, h):
        img_numpy = img
        return img_numpy

    def display_lincomb(self,proto_data, masks):
        out_masks = torch.matmul(proto_data, masks.t())
        # out_masks = cfg.mask_proto_mask_activation(out_masks)

        for kdx in range(1):
            jdx = kdx + 0
            import matplotlib.pyplot as plt
            coeffs = masks[jdx, :].cpu().numpy()
            idx = np.argsort(-np.abs(coeffs))
            # plt.bar(list(range(idx.shape[0])), coeffs[idx])
            # plt.show()
            
            coeffs_sort = coeffs[idx]
            arr_h, arr_w = (4,8)
            proto_h, proto_w, _ = proto_data.size()
            arr_img = np.zeros([proto_h*arr_h, proto_w*arr_w])
            arr_run = np.zeros([proto_h*arr_h, proto_w*arr_w])
            test = torch.sum(proto_data, -1).cpu().numpy()

            for y in range(arr_h):
                for x in range(arr_w):
                    i = arr_w * y + x

                    if i == 0:
                        running_total = proto_data[:, :, idx[i]].cpu().numpy() * coeffs_sort[i]
                    else:
                        running_total += proto_data[:, :, idx[i]].cpu().numpy() * coeffs_sort[i]

                    running_total_nonlin = running_total
                    if cfg.mask_proto_mask_activation == activation_func.sigmoid:
                        running_total_nonlin = (1/(1+np.exp(-running_total_nonlin)))

                    arr_img[y*proto_h:(y+1)*proto_h, x*proto_w:(x+1)*proto_w] = (proto_data[:, :, idx[i]] / torch.max(proto_data[:, :, idx[i]])).cpu().numpy() * coeffs_sort[i]
                    arr_run[y*proto_h:(y+1)*proto_h, x*proto_w:(x+1)*proto_w] = (running_total_nonlin > 0.5).astype(np.float)
            plt.imshow(arr_img)
            plt.show()
            # plt.imshow(arr_run)
            # plt.show()
            # plt.imshow(test)
            # plt.show()
            plt.imshow(out_masks[:, :, jdx].cpu().numpy())
            plt.show()

    def postprocess(self,det_output, w, h, batch_idx=0, interpolation_mode='bilinear',
                    visualize_lincomb=False, crop_masks=True, score_threshold=0):
        """
        Postprocesses the output of Yolact on testing mode into a format that makes sense,
        accounting for all the possible configuration settings.

        Args:
            - det_output: The lost of dicts that Detect outputs.
            - w: The real with of the image.
            - h: The real height of the image.
            - batch_idx: If you have multiple images for this batch, the image's index in the batch.
            - interpolation_mode: Can be 'nearest' | 'area' | 'bilinear' (see torch.nn.functional.interpolate)

        Returns 4 torch Tensors (in the following order):
            - classes [num_det]: The class idx for each detection.
            - scores  [num_det]: The confidence score for each detection.
            - boxes   [num_det, 4]: The bounding box for each detection in absolute point form.
            - masks   [num_det, h, w]: Full image masks for each detection.
        """
        
        dets = det_output[batch_idx]
        net = dets['net']
        dets = dets['detection']
        cfg.mask_proto_debug = False 
        if dets is None:
            return [torch.Tensor()] * 4 # Warning, this is 4 copies of the same thing

        if score_threshold > 0:
            keep = dets['score'] > score_threshold

            for k in dets:
                if k != 'proto':
                    dets[k] = dets[k][keep]
            
            if dets['score'].size(0) == 0:
                return [torch.Tensor()] * 4
        
        # Actually extract everything from dets now
        classes = dets['class']
        boxes   = dets['box']
        scores  = dets['score']
        masks   = dets['mask']

        if cfg.mask_type == mask_type.lincomb and cfg.eval_mask_branch:
            # At this points masks is only the coefficients
            proto_data = dets['proto']
            
            # Test flag, do not upvote
            if cfg.mask_proto_debug:
                np.save('scripts/proto.npy', proto_data.cpu().numpy())
            
            if visualize_lincomb:
                self.display_lincomb(proto_data, masks)

            masks = proto_data @ masks.t()
            masks = cfg.mask_proto_mask_activation(masks)

            # Crop masks before upsampling because you know why
            if crop_masks:
                masks = crop(masks, boxes)

            # Permute into the correct output shape [num_dets, proto_h, proto_w]
            masks = masks.permute(2, 0, 1).contiguous()

            if cfg.use_maskiou:
                with timer.env('maskiou_net'):                
                    with torch.no_grad():
                        maskiou_p = net.maskiou_net(masks.unsqueeze(1))
                        maskiou_p = torch.gather(maskiou_p, dim=1, index=classes.unsqueeze(1)).squeeze(1)
                        if cfg.rescore_mask:
                            if cfg.rescore_bbox:
                                scores = scores * maskiou_p
                            else:
                                scores = [scores, scores * maskiou_p]

            # Scale masks up to the full image
            masks = F.interpolate(masks.unsqueeze(0), (h, w), mode=interpolation_mode, align_corners=False).squeeze(0)

            # Binarize the masks
            masks.gt_(0.5)

        
        boxes[:, 0], boxes[:, 2] = sanitize_coordinates(boxes[:, 0], boxes[:, 2], w, cast=False)
        boxes[:, 1], boxes[:, 3] = sanitize_coordinates(boxes[:, 1], boxes[:, 3], h, cast=False)
        boxes = boxes.long()

        if cfg.mask_type == mask_type.direct and cfg.eval_mask_branch:
            # Upscale masks
            full_masks = torch.zeros(masks.size(0), h, w)

            for jdx in range(masks.size(0)):
                x1, y1, x2, y2 = boxes[jdx, :]

                mask_w = x2 - x1
                mask_h = y2 - y1

                # Just in case
                if mask_w * mask_h <= 0 or mask_w < 0:
                    continue
                
                mask = masks[jdx, :].view(1, 1, cfg.mask_size, cfg.mask_size)
                mask = F.interpolate(mask, (mask_h, mask_w), mode=interpolation_mode, align_corners=False)
                mask = mask.gt(0.5).float()
                full_masks[jdx, y1:y2, x1:x2] = mask
            
            masks = full_masks

        return classes, scores, boxes, masks

    def prep_display(self,dets_out, img, h, w, undo_transform=True, class_color=False, mask_alpha=0.45):
        """
        Prepare final output as an image, given post-processed prediction results.
        """
        top_k = 10

        if undo_transform:
            img_numpy = self.undo_image_transformation(img, w, h)
            img_gpu = torch.Tensor(img_numpy).cuda()
        else:
            img_gpu = img / 255.0
            h, w, _ = img.shape

        with timer.env('Postprocess'):
            t = self.postprocess(dets_out, w, h, visualize_lincomb=False, crop_masks=True, score_threshold=0)

        idx = t[1].argsort(0, descending=True)[:top_k]
        classes, scores, boxes, masks = [x[idx].cpu().detach().numpy() for x in t[:4]]


        num_dets_to_consider = min(top_k, classes.shape[0])
        for j in range(num_dets_to_consider):
            if scores[j] < 0.2:
                num_dets_to_consider = j
                break

        detected_info = {}
        for j in range(num_dets_to_consider):
            x1, y1, x2, y2 = boxes[j]
            
            color = COLORS[classes[j] % len(COLORS)]
            
            cv2.rectangle(img_numpy, (x1, y1), (x2, y2), color, 2)
            
            _class = cfg.dataset.class_names[classes[j]]
            detected_info[_class] = (x1, y1, x2, y2)
            
            text_str = _class
            
            font_face = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.6
            font_thickness = 1

            text_w, text_h = cv2.getTextSize(text_str, font_face, font_scale, font_thickness)[0]
            text_pt = (x1, y1 - 3)

            cv2.rectangle(img_numpy, (x1, y1), (x1 + text_w, y1 - text_h - 4), color, -1)
            cv2.putText(img_numpy, text_str, text_pt, font_face, font_scale, [255, 255, 255], font_thickness, cv2.LINE_AA)

            # Mask overlay
            mask = masks[j]
            
            mask = cv2.resize(mask, (w, h))
            
            img_numpy[mask > 0.5] = (1 - mask_alpha) * img_numpy[mask > 0.5] + mask_alpha * np.array(color)
                
        return img_numpy, detected_info
    def run(self):
        video_capture = cv2.VideoCapture(0)  # 0 for default camera

        if not video_capture.isOpened():
            print('Error: Could not open video.')
            exit(-1)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to grab frame")
                break

            h, w, _ = frame.shape
            
            frame_tensor = torch.from_numpy(frame).cuda().float()
            frame_tensor = FastBaseTransform()(frame_tensor.unsqueeze(0))
            preds = self.model(frame_tensor)
            display_frame, detected_info = self.prep_display(preds, frame, h, w)

            # detected_info 딕셔너리를 이용하여 추가적인 처리를 수행할 수 있습니다.
            for class_name, bbox in detected_info.items():
                print(f"Class: {class_name}, Bbox: {bbox}")
            
            cv2.imshow('YOLACT Real-time Detection', display_frame)

            # 'q' 키를 누르면 종료합니다.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
if __name__ == '__main__':
    detector = YolactRealtimeDetection()
    detector.run()
