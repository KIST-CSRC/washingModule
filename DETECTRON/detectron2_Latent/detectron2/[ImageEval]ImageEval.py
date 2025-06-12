import cv2
import os, sys
sys.path.append("./detectron2")
import detectron2
import torch
from detectron2.utils.logger import setup_logger
setup_logger()
from detectron2 import model_zoo
from detectron2.engine.defaults import DefaultPredictor, LatentRCNNPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.data.datasets import register_coco_instances
import matplotlib.pyplot as plt
from yacs.config import CfgNode as CN
from detectron2.modeling.latent import Prior, Encoder
from detectron2.modeling import build_backbone,build_model
from detectron2.checkpoint import DetectionCheckpointer
import detectron2.data.transforms as T

dataset_dir = "C:/Users/LHS/Desktop/DETECTRON/Data/safetyCOCO"
# Register the datasets using COCO format
register_coco_instances("my_custom_train", {}, os.path.join(dataset_dir, "train/train.json"), os.path.join(dataset_dir, "train"))
register_coco_instances("my_custom_val", {}, os.path.join(dataset_dir, "val/val.json"), os.path.join(dataset_dir, "val"))

# Configure the model settings
def setup_config():
    cfg = get_cfg()
    cfg.merge_from_file("detectron2/configs/latent/latent_mrcnn_coco.yaml")

    cfg.MODEL.WEIGHTS = "./detectron2_Latent/output/Latent_20250109_KL_Washing_LDH_IR/model_final.pth" #
    cfg.DATASETS.TRAIN = ("my_custom_train",)
    cfg.DATASETS.TEST = ("my_custom_val",)
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 5
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.KL = CN()  
    cfg.MODEL.KL.Z_DIM = 64 
    cfg.MODEL.KL.POSITION = True  
    cfg.MODEL.KL.LEARNED_PRIOR = True 
    cfg.MODEL.KL.LOSS = True
    cfg.MODEL.KL.CONST_SCALE = 1e-5
    # Define custom configuration parameters
    cfg.AGREEMENT = get_cfg()  # Create a nested config
    cfg.AGREEMENT.NSAMPLES = 10
    cfg.AGREEMENT.AUGMENTATIONS = ["none"]
    cfg.AGREEMENT.MODE = "agree"
    cfg.AGREEMENT.DEVICE = "cuda"
    cfg.AGREEMENT.MAX_INSTANCES = 256
    cfg.AGREEMENT.SCORE_THRESHOLD = 0.5
    cfg.AGREEMENT.NMS_THRESHOLD = 0.5
    cfg.AGREEMENT.MIN_AREA = 0.01
    cfg.AGREEMENT.THRESHOLD = 0.5
    return cfg

cfg = setup_config() 
image_path = "Input Your Image Path"

image = cv2.imread(image_path)

predictor = LatentRCNNPredictor(cfg)
predictions,uncertainty = predictor.uncertainties_inference(image)

print(uncertainty[-1])

thing_classes = ["holder","falcon","liquid",'precipitate']
thing_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),(255,255,255)] 
MetadataCatalog.get("my_custom_val").set(thing_classes=thing_classes, thing_colors=thing_colors)
metadata = MetadataCatalog.get("my_custom_val")

class_filter = ["liquid", "precipitate"]
class_filter_ids = [thing_classes.index(cls) for cls in class_filter]
instances = predictions["instances"].to("cpu")
keep = [i for i, cls in enumerate(instances.pred_classes) if cls in class_filter_ids]
filtered_instances = instances[keep]

v = Visualizer(image[:, :, ::-1], metadata, scale=1.2, instance_mode=ColorMode.SEGMENTATION)
v = v.draw_instance_predictions(predictions["instances"].to("cpu"))
result_image = v.get_image()[:, :, ::-1].astype("uint8") 

cv2.imshow("Predicted Image with Uncertainty", result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()


