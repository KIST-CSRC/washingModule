# 데이터셋과 모델 로드
from detectron2.data import build_detection_test_loader
from detectron2.engine.defaults import DefaultPredictor, LatentRCNNPredictor

import cv2
import os
from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2 import model_zoo
from detectron2.engine.defaults import LatentRCNNPredictor
from detectron2.evaluation.intersection_evaluation import IntersectionEvaluator
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.data.datasets import register_coco_instances
import matplotlib.pyplot as plt
from yacs.config import CfgNode as CN
dataset_dir = "C:/Users/LHS/Desktop/DETECTRON/Data/WashingData/LDH_Ir_Washing_1926_250103_gray"

# Register the datasets using COCO format
register_coco_instances("my_custom_train", {}, os.path.join(dataset_dir, "train/train.json"), os.path.join(dataset_dir, "train"))
register_coco_instances("my_custom_val", {}, os.path.join(dataset_dir, "val/val.json"), os.path.join(dataset_dir, "val"))

# Configure the model settings
def setup_config():
    cfg = get_cfg()
    cfg.merge_from_file("detectron2/configs/latent/latent_mrcnn_coco.yaml")
    cfg.MODEL.WEIGHTS = "C:/Users/LHS/Desktop/DETECTRON/detectron2_Latent/output/Latent_20250103_KL_Washing_LDH_IR/model_final.pth"
    cfg.DATASETS.TRAIN = ("my_custom_train",)
    cfg.DATASETS.TEST = ("my_custom_val",)
    
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.1
    cfg.MODEL.KL = CN()  # CN()은 yacs 라이브러리의 ConfigNode를 생성합니다.
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
    
    cfg.SOLVER.IMS_PER_BATCH = 2
    cfg.SOLVER.BASE_LR = 0.0025
    cfg.SOLVER.MAX_ITER = 10000  # 조정 가능
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 512
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 5  # 클래스 수 조정 필요
    cfg.SOLVER.WARMUP_ITERS = 1000  
    return cfg
cfg = setup_config()
predictor = LatentRCNNPredictor(cfg)

evaluator = IntersectionEvaluator(dataset_name="my_custom_val", output_folder="./output/Latent/Eval/20250103_gray")

# 평가기 초기화
from detectron2.data import build_detection_test_loader
data_loader = build_detection_test_loader(cfg, "my_custom_val",num_workers=0)
for inputs in data_loader:
    print(inputs)

    outputs = predictor(inputs)
    evaluator.process(inputs, outputs)
evaluator.evaluate()
