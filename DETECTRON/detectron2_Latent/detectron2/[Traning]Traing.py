import os, sys
sys.path.append("./detectron2")
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()
import datetime
from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer,DefaultPredictor
from detectron2.config import get_cfg
from detectron2.evaluation.intersection_evaluation import IntersectionEvaluator
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from yacs.config import CfgNode as CN
from detectron2.data.datasets import register_coco_instances
dataset_dir = "Input Your Dataset"
register_coco_instances("my_dataset_train", {}, os.path.join(dataset_dir, "train/train.json"), os.path.join(dataset_dir, "train"))
register_coco_instances("my_dataset_val", {}, os.path.join(dataset_dir, "test/test.json"), os.path.join(dataset_dir, "test"))
cfg = get_cfg()
cfg.merge_from_file("detectron2/configs/latent/latent_mrcnn_coco.yaml")
cfg.DATASETS.TRAIN = ("my_dataset_train",)
cfg.DATASETS.VAL = ("my_dataset_val",)
cfg.DATALOADER.NUM_WORKERS = 0
cfg.MODEL.KL = CN()  # 
cfg.MODEL.KL.Z_DIM = 64 
cfg.MODEL.KL.POSITION = True  
cfg.MODEL.KL.CONST_SCALE = 1e-5
cfg.MODEL.KL.LEARNED_PRIOR = True 
cfg.MODEL.KL.LOSS = True
cfg.AGREEMENT = get_cfg()
cfg.AGREEMENT.NSAMPLES = 10
print("Current KL configuration:", cfg.MODEL.KL)
cfg.MODEL.WEIGHTS =  "Input Your Trained model"
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.0025
cfg.SOLVER.MAX_ITER = 10000 
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 512
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 5 
cfg.SOLVER.WARMUP_ITERS = 1000  
today_date = datetime.datetime.now().strftime("%Y%m%d")
cfg.OUTPUT_DIR = f"./output/Latent_{today_date}_KL_Washing_LDH_IR_QD"

os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg)
trainer.resume_or_load(resume=False)
trainer.train()
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
predictor = DefaultPredictor(cfg)
evaluator = IntersectionEvaluator(dataset_name="my_custom_val", output_folder="./output/Latent/Eval_20250109")
from detectron2.data import build_detection_test_loader
data_loader = build_detection_test_loader(cfg, "my_custom_val",num_workers=0)
for inputs in data_loader:
    print(inputs)

    outputs = predictor(inputs)
    evaluator.process(inputs, outputs)
evaluator.evaluate()
