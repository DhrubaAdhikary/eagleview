#!/bin/bash
python /eagleview/yolov5/val.py --weights /content/best.pt --data eagleview.yaml --task test --name yolo_det