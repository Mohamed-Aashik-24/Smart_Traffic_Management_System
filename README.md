# AI_traffic_management_system — Traffic vehicle detection

This project contains scripts to detect vehicles in images (inference) and to auto-label images using a pretrained YOLOv8 model to prepare a YOLO-format dataset for training.

What’s included
- `model detection.py` — Run inference on all images in the `Traffic vehicle` folder, print per-image vehicle counts, save annotated images to `outputs/` and display them one-by-one.
- (Optional) `auto_label.py` — Script to pseudo-label images using a pretrained YOLO model (if present).
- `requirements.txt` — Python dependencies for inference and auto-label workflows.

Quick start (Windows PowerShell)

1) Create a virtual environment and install dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -U pip; pip install -r requirements.txt
```

2) Run inference on images in the `Traffic vehicle` folder

```powershell
python "model detection.py"
```

3) (Optional) Auto-label images to create a YOLO dataset

```powershell
python auto_label.py
```

4) (Optional) Train a YOLOv8 model (after labels exist)

```powershell
# Example using Ultralytics CLI (adjust parameters as needed):
yolo task=detect mode=train model=yolov8s.pt data=dataset/data.yaml epochs=50 imgsz=640
```

Notes
- The inference script uses a pretrained YOLOv8 model and maps common COCO vehicle classes (car, motorcycle, bus, truck, bicycle).
- The auto-label workflow (pseudo-labeling) is a convenience to bootstrap annotations — manual correction improves final model quality.
