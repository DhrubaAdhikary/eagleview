#!/bin/bash
python /eagleview/yolov5/train.py --img 640 --cfg yolov5s.yaml --hyp hyp.scratch.yaml --batch 32 --epochs 50 --data eagleview.yaml --weights yolov5s.pt --workers 24 --name yolo_eagle_det