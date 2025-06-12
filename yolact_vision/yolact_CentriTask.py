import os, sys
from datetime import datetime
import sys
from chardet import detect
from matplotlib.pyplot import box
sys.path.append("/home/preprocess/catkin_ws/src/doosan-robot/yolact_vision/")
sys.path.append("/home/preprocess/catkin_ws/src/doosan-robot/")

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import cv2
import numpy as np
import torch
from data import mask_type, MEANS, STD, activation_func, COLORS
from data.config_centri import set_cfg, cfg
from utils.augmentations import Resize
from utils import timer
from layers.box_utils import crop, sanitize_coordinates
from utils.augmentations import FastBaseTransform
from yolact_Centri_origin import Yolact
from pycocotools import coco
import torch.nn.functional as F
import math
class YolactCentrifugeTask:

    def __init__(self, model_path="./yolact_vision/weights/yolact_base_34_3000.pth"):
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

        for kdx in range(1):
            jdx = kdx + 0
            import matplotlib.pyplot as plt
            coeffs = masks[jdx, :].cpu().numpy()
            idx = np.argsort(-np.abs(coeffs))
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
            return [torch.Tensor()] * 4 

        if score_threshold > 0:
            keep = dets['score'] > score_threshold

            for k in dets:
                if k != 'proto':
                    dets[k] = dets[k][keep]
            
            if dets['score'].size(0) == 0:
                return [torch.Tensor()] * 4
        
        
        classes = dets['class']
        boxes   = dets['box']
        scores  = dets['score']
        masks   = dets['mask']

        if cfg.mask_type == mask_type.lincomb and cfg.eval_mask_branch:
            
            proto_data = dets['proto']
            
            
            if cfg.mask_proto_debug:
                np.save('scripts/proto.npy', proto_data.cpu().numpy())
            
            if visualize_lincomb:
                self.display_lincomb(proto_data, masks)

            masks = proto_data @ masks.t()
            masks = cfg.mask_proto_mask_activation(masks)

            
            if crop_masks:
                masks = crop(masks, boxes)

            
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

            
            masks = F.interpolate(masks.unsqueeze(0), (h, w), mode=interpolation_mode, align_corners=False).squeeze(0)

            
            masks.gt_(0.5)

        
        boxes[:, 0], boxes[:, 2] = sanitize_coordinates(boxes[:, 0], boxes[:, 2], w, cast=False)
        boxes[:, 1], boxes[:, 3] = sanitize_coordinates(boxes[:, 1], boxes[:, 3], h, cast=False)
        boxes = boxes.long()

        if cfg.mask_type == mask_type.direct and cfg.eval_mask_branch:
            
            full_masks = torch.zeros(masks.size(0), h, w)

            for jdx in range(masks.size(0)):
                x1, y1, x2, y2 = boxes[jdx, :]

                mask_w = x2 - x1
                mask_h = y2 - y1

                
                if mask_w * mask_h <= 0 or mask_w < 0:
                    continue
                
                mask = masks[jdx, :].view(1, 1, cfg.mask_size, cfg.mask_size)
                mask = F.interpolate(mask, (mask_h, mask_w), mode=interpolation_mode, align_corners=False)
                mask = mask.gt(0.5).float()
                full_masks[jdx, y1:y2, x1:x2] = mask
            
            masks = full_masks

        return classes, scores, boxes, masks



    def detect_color_hsv(self, frame, color):
        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv_image = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)

        if color == 'red':
            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
            mask = mask1 + mask2
        elif color == 'blue':
            lower_blue = np.array([100, 100, 100])
            upper_blue = np.array([140, 255, 255])
            mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
        elif color == 'yellow':
            lower_yellow = np.array([25, 100, 100])
            upper_yellow = np.array([30, 255, 255])
            mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
        else:
            return None
        return mask, cv2.bitwise_and(frame, frame, mask=mask)
    

    def draw_top_contours(self, frame, mask, min_area=100, top=3):
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
        large_contours = sorted(large_contours, key=cv2.contourArea, reverse=True)[:top]

        boxes = []
        for contour in large_contours:
            x, y, w, h = cv2.boundingRect(contour)
            x2, y2 = x + w, y + h
            cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
            boxes.append((x, y, x2, y2))

        return frame, boxes
        
    def color_location(self):
        cap = cv2.VideoCapture(0)

        named_classes_locations = {}
        color_box = {}

        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame from camera.")
                    break

                h, w = frame.shape[:2]
                frame_tensor = torch.from_numpy(frame).cuda().float()
                frame_tensor = FastBaseTransform()(frame_tensor.unsqueeze(0))
                preds = self.model(frame_tensor)

                
                display_frame, _, classes_locations, color_box_dict = self.prep_display_test(
                    preds, frame, h, w
                )
                for class_id, boxes in classes_locations.items():
                    class_name = cfg.dataset.class_names[class_id]
                    named_classes_locations.setdefault(class_name, []).extend(boxes)
                for color_k, color_v in color_box_dict.items():
                    color_box[color_k] = color_v
               
                break

        cap.release()       
        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_filename = f"DB/Results/Centri/CentriTask_{now_str}.jpg"
        save_path = os.path.join(".", save_filename)
        cv2.imwrite(save_path, display_frame)
        print(f"[INFO] Detection image saved: {save_path}")

        return named_classes_locations, color_box

    def prep_display_test(self, dets_out, img, h, w, undo_transform=True, class_color=False, mask_alpha=0.45):
        """
        Prepare final output as an image, given post-processed prediction results.
        Returns (img_numpy, boxes_to_return, classes_location, color_boxes).
        """
        top_k = 10
        if undo_transform:
            img_numpy = self.undo_image_transformation(img, w, h)
        else:
            img_numpy = img  

        with timer.env('Postprocess'):
            t = self.postprocess(
                dets_out, w, h,
                visualize_lincomb=False,
                crop_masks=True,
                score_threshold=0
            )
        classes, scores, boxes, masks = [x.cpu().numpy() for x in t]
        idx = scores.argsort()[::-1][:top_k]
        classes = classes[idx]
        scores  = scores[idx]
        boxes   = boxes[idx]
        masks   = masks[idx]
        num_dets_to_consider = 0
        for i in range(len(scores)):
            if scores[i] >= 0.2:
                num_dets_to_consider += 1
            else:
                break
        color_boxes = {}
        for color in ['blue', 'yellow']:
            mask_color, _ = self.detect_color_hsv(img, color)
            img, color_box = self.draw_top_contours(img, mask_color, 3)
            color_boxes[color] = color_box
        classes_location = {}
        boxes_to_return  = []

        for j in range(num_dets_to_consider):
            class_id = classes[j]
            score    = scores[j]
            x1, y1, x2, y2 = boxes[j]
            
            
            color = COLORS[class_id % len(COLORS)]
            mask  = masks[j]
            mask  = cv2.resize(mask, (w, h))
            img_numpy[mask > 0.5] = (1 - mask_alpha) * img_numpy[mask > 0.5] + mask_alpha * np.array(color)
            class_name = cfg.dataset.class_names[class_id]  
            text_str   = f"{class_name}"  
            font_face = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 1
            text_size, _ = cv2.getTextSize(text_str, font_face, font_scale, font_thickness)
            text_x, text_y = x1, max(y1 - 1, 0)       
            cv2.rectangle(
                img_numpy,
                (text_x, text_y - text_size[1]),
                (text_x + text_size[0], text_y),
                color, -1
            )
            
            cv2.putText(
                img_numpy, text_str,
                (text_x, text_y),
                font_face, font_scale, (255, 255, 255),
                font_thickness, cv2.LINE_AA
            )

            
            boxes_to_return.append((x1, y1, x2, y2))
            if class_id not in classes_location:
                classes_location[class_id] = []
            classes_location[class_id].append((x1, y1, x2, y2))

        return img_numpy, boxes_to_return, classes_location, color_boxes

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
        classes, scores, boxes, masks = [x[idx].cpu().numpy() for x in t[:4]]

        num_dets_to_consider = min(top_k, classes.shape[0])
        for j in range(num_dets_to_consider):
            if scores[j] < 0.2:
                num_dets_to_consider = j
                break
        boxes_to_return = []
        classes_location = {}
        for color in ['blue', 'yellow']:     
            mask, _ = self.detect_color_hsv(img, color)
            img = self.draw_top_contours(img, mask, 3)               
        for j in range(num_dets_to_consider):
            x1, y1, x2, y2 = boxes[j]
            boxes_to_return.append((x1, y1, x2, y2))
            class_key = classes[j]
            if class_key not in classes_location:
                classes_location[class_key] = []
            classes_location[class_key].append((x1, y1, x2, y2))
        
            color = COLORS[classes[j] % len(COLORS)]
                     
            _class = cfg.dataset.class_names[classes[j]]
            text_str = _class
           
            font_face = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.75
            font_thickness = 1
            text_w, text_h = cv2.getTextSize(text_str, font_face, font_scale, font_thickness)[0]
            text_pt = (x1, y1 - 3)

            mask = masks[j]
            mask = cv2.resize(mask, (w, h))
            img_numpy[mask > 0.5] = (1 - mask_alpha) * img_numpy[mask > 0.5] + mask_alpha * np.array(color)

        return img_numpy, boxes_to_return,classes_location

    def calculate_center(self,box):
        x1, y1, x2, y2 = box
        return (x1 + x2) / 2, (y1 + y2) / 2

        
    def calculate_angle(self,center, color_center):
        dx = -center[0] + color_center[0]
        dy = - color_center[1]+ center[1] 
        angle_rad = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
        return angle_deg
    
    def center_of_object(self,obj):
        x1, y1, x2, y2 = obj
        return (x1 + x2) / 2, (y1 + y2) / 2

    def color_location_to_angle(self, named_classes_locations, color_box):
        """
        Sort objects based on their proximity to specified color boxes.
        Excludes 'rotor' objects and sorts 'hole' objects.
        :param named_classes_locations: Dictionary of objects with their locations.
        :param color_box: Dictionary of color boxes with their locations.
        :return: List of tuples, each containing an object's identifier and its center, sorted based on color proximity.
        """
    
        rotor_center = self.center_of_object(named_classes_locations['rotor'][0])

        
        color_centers = {color: self.calculate_center(box[0]) for color, box in color_box.items()}

        
        angles_relative_to_rotor = {}
        for color, center in color_centers.items():
            angle = self.calculate_angle(rotor_center, center)
            angles_relative_to_rotor[color] = angle

        return angles_relative_to_rotor

    def sort_objects_by_angle_to_color(self, named_classes_locations, color_box):
        
        red_center = self.calculate_center(color_box['blue'][0])
        rotor_center = self.calculate_center(named_classes_locations['rotor'][0])
        red_angle = self.calculate_angle(rotor_center, red_center)
        
        object_angles_with_key = []
        for key, locations in named_classes_locations.items():
            if key != 'rotor':  
                for location in locations:
                    center = self.center_of_object(location)
                    angle = self.calculate_angle(rotor_center, center)
                    object_angles_with_key.append((key, center, round(angle,2)))
        
        def angle_difference(angle):
            diff = red_angle - angle
            
            diff = diff if diff >= 0 else diff + 360
            return round(diff, 2)
        sorted_objects_by_angle = sorted(object_angles_with_key, key=lambda x: angle_difference(x[2]))
 
        sorted_objects_by_type = {
            'hole': [(item[1], item[2]) for item in sorted_objects_by_angle if item[0] == 'hole'],
            'falcon': [(item[1], item[2]) for item in sorted_objects_by_angle if item[0] == 'falcon']
            
        }
        return sorted_objects_by_type
    def object_convertoangle(self, named_classes_locations, color_box):
        
        blue_center = self.calculate_center(color_box['blue'][0])
        rotor_center = self.calculate_center(named_classes_locations['rotor'][0])
        blue_angle = self.calculate_angle(rotor_center, blue_center)
        
        object_angles_with_key = []
        for key, locations in named_classes_locations.items():
            if key != 'rotor':  
                for location in locations:
                    center = self.center_of_object(location)
                    angle = self.calculate_angle(rotor_center, center)
                    object_angles_with_key.append((key, round(angle,2)))
        def angle_difference(angle):
            diff = blue_angle - angle
            diff = diff if diff >= 0 else diff + 360
            return round(diff, 2)
        sorted_objects_by_angle = sorted(object_angles_with_key, key=lambda x: angle_difference(x[1]))
        adjusted_objects_by_angle = [(obj_type, round((angle + 360) % 360, 2)) for obj_type, angle in sorted_objects_by_angle]
        sorted_objects_by_type = {
            'hole': [item[1] for item in adjusted_objects_by_angle if item[0] == 'hole'],
            'falcon': [item[1] for item in adjusted_objects_by_angle if item[0] == 'falcon']
        
        }
        return sorted_objects_by_type

    def convert_robot_coordinates(self,task):
        
        named_classes_locations,color_box =self.color_location()
        sort_objects_by_angle = self.object_convertoangle(named_classes_locations,color_box)
        if task == 'Place':            
            base_tuple = (-358.280, -540.600, 375.00, 90, 186, 90)
        elif task == 'Pick':
            base_tuple = (-358.280, -540.000, 190.00, 90, 188.90, 90)
        transformto_robotcoordi = {}
        for class_name, angle_list in sort_objects_by_angle.items():
            transformto_robotcoordi[class_name] = []
            for angle in angle_list:
                new_tuple = base_tuple[:3] + (angle,) + base_tuple[4:]
                transformto_robotcoordi[class_name].append(new_tuple)
        return transformto_robotcoordi                        
    def run_test_angle(self):
        cap = cv2.VideoCapture(0)           
        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                h, w = frame.shape[:2]
                orgin_frame = frame.copy()
                frame_tensor = torch.from_numpy(frame).cuda().float()
                frame_tensor = FastBaseTransform()(frame_tensor.unsqueeze(0))
                preds = self.model(frame_tensor)
                display_frame, box, classes_locations, color_box = self.prep_display_test(preds, frame, h, w)
                named_classes_locations = {}
                for class_id, boxes in classes_locations.items():
                    class_name = cfg.dataset.class_names[class_id]  
                    named_classes_locations[class_name] = boxes
                sorted_centers = self.sort_objects_by_angle_to_color(named_classes_locations, color_box)
                if 'hole' in sorted_centers:
                    for idx, (center, angle) in enumerate(sorted_centers['hole']):
                        cv2.putText(display_frame, f'H{idx + 1}', (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        angle_text = f'{angle:.2f}'
                if 'falcon' in sorted_centers:
                    for idx, (center, angle)  in enumerate(sorted_centers['falcon']):              
                        cv2.putText(display_frame, f'F{idx + 1}', (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        angle_text = f'{angle:.2f}'                                            
                cv2.imshow('YOLACT Real-time Detection', display_frame)
                cv2.imshow('origin', orgin_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    def run_test(self):
        cap = cv2.VideoCapture(0)           
        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                h, w = frame.shape[:2]
                orgin_frame = frame.copy()
                frame_tensor = torch.from_numpy(frame).cuda().float()
                frame_tensor = FastBaseTransform()(frame_tensor.unsqueeze(0))
                preds = self.model(frame_tensor)
                display_frame, box, classes_locations, color_box = self.prep_display_test(preds, frame, h, w)
                named_classes_locations = {}
                for class_id, _ in classes_locations.items():
                    class_name = cfg.dataset.class_names[class_id]  
                    named_classes_locations[class_name] = _
                sorted_centers = self.sort_objects_by_color(named_classes_locations, color_box)
                if 'hole' in sorted_centers:
                    for idx, center in enumerate(sorted_centers['hole']):
                        cv2.putText(display_frame, f'H{idx + 1}', (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if 'falcon' in sorted_centers:
                    for idx, center in enumerate(sorted_centers['falcon']):
                        cv2.putText(display_frame, f'F{idx + 1}', (int(center[0]), int(center[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.imshow('YOLACT Real-time Detection', display_frame)
                cv2.imshow('origin', orgin_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    def run_realtime(self):
        cap = cv2.VideoCapture(0)   
        save_dir = "saved_frames"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with torch.no_grad():
            while True:
                ret, frame = cap.read()
                h, w = frame.shape[:2]
                orgin_frame = frame.copy()
                frame_tensor = torch.from_numpy(frame).cuda().float()
                frame_tensor = FastBaseTransform()(frame_tensor.unsqueeze(0))
                preds = self.model(frame_tensor)
                display_frame,box,classes_locations = self.prep_display(preds, frame, h, w)
                if len(classes_locations) >= 7:
                    for box, class_id in zip(classes_locations, preds[0]['detection']['class']):
                        class_name = cfg.dataset.class_names[class_id]
                        
                        if class_name not in classes_locations:
                            classes_locations[class_name] = []

                        
                        classes_locations[class_name].append(box)
                    print(classes_locations)
                    
                    today = datetime.today().strftime('%Y-%m-%d')
                    current_time = datetime.now().strftime('%H-%M-%S')

                    
                    directory_path = os.path.join("capture", today)
                    if not os.path.exists(directory_path):  
                        os.makedirs(directory_path)

                    save_path = os.path.join(directory_path, f"{current_time}.jpg")
                    cv2.imwrite(save_path, display_frame)
                    break

                print(classes_locations)
                cv2.imshow('YOLACT Real-time Detection', display_frame)
                cv2.imshow('origin', orgin_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

if __name__ == '__main__':
    detector = YolactCentrifugeTask()
    named_classes_locations,color_box =detector.color_location()
    detector.run_test_angle()
     
    
    
    
    
    
    
    
    
    
    
    
    
    
