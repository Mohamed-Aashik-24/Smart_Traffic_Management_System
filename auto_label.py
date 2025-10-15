import os
import random
from pathlib import Path
import sys

try:
    from ultralytics import YOLO
except Exception as e:
    print("ultralytics not installed. Install with: pip install -r requirements.txt")
    raise

import cv2


IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.avif', '.tif', '.tiff'}


def find_images(src_dir):
    p = Path(src_dir)
    return [str(x) for x in p.iterdir() if x.suffix.lower() in IMAGE_EXTS and x.is_file()]


def ensure_dirs(base_dir):
    base = Path(base_dir)
    (base / 'images' / 'train').mkdir(parents=True, exist_ok=True)
    (base / 'images' / 'val').mkdir(parents=True, exist_ok=True)
    (base / 'labels' / 'train').mkdir(parents=True, exist_ok=True)
    (base / 'labels' / 'val').mkdir(parents=True, exist_ok=True)


# Mapping from COCO class IDs to our label indices
# COCO IDs: 1=bicycle,2=car,3=motorcycle,5=bus,7=truck
COCO_TO_LABEL = {
    2: 0,  # car -> 0
    3: 1,  # motorcycle -> 1
    5: 2,  # bus -> 2
    7: 3,  # truck -> 3
    1: 4,  # bicycle -> 4
}

LABEL_NAMES = ['car', 'motorcycle', 'bus', 'truck', 'bicycle']


def xyxy_to_yolo(x1, y1, x2, y2, img_w, img_h):
    # convert to x_center, y_center, w, h normalized
    xc = (x1 + x2) / 2.0
    yc = (y1 + y2) / 2.0
    w = x2 - x1
    h = y2 - y1
    return xc / img_w, yc / img_h, w / img_w, h / img_h


def save_label_file(label_path, detections):
    # detections: list of (class_id, x_center, y_center, w, h)
    with open(label_path, 'w') as f:
        for cls, xc, yc, w, h in detections:
            f.write(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")


def main():
    # Paths
    workspace = Path(__file__).parent
    src_images_dir = workspace / 'Traffic vehicle'
    dataset_dir = workspace / 'dataset'

    if not src_images_dir.exists():
        print(f"Source images folder not found: {src_images_dir}")
        sys.exit(1)

    print(f"Searching images in: {src_images_dir}")
    images = find_images(src_images_dir)
    if not images:
        print("No images found to label. Supported extensions:", IMAGE_EXTS)
        sys.exit(1)

    # Train/val split
    random.seed(42)
    random.shuffle(images)
    split_idx = max(1, int(0.9 * len(images)))
    train_imgs = images[:split_idx]
    val_imgs = images[split_idx:]

    ensure_dirs(dataset_dir)

    print(f"Found {len(images)} images. Train: {len(train_imgs)}, Val: {len(val_imgs)}")

    # Load YOLO model (pretrained)
    print("Loading YOLO model (this will download weights if not present)...")
    model = YOLO('yolov8n.pt')

    def process_list(img_list, split):
        for src in img_list:
            src_path = Path(src)
            try:
                img = cv2.imread(str(src_path))
                if img is None:
                    print(f"Skipping unreadable image: {src_path.name}")
                    continue
                h, w = img.shape[:2]
            except Exception as e:
                print(f"Error reading {src_path}: {e}")
                continue

            # Copy image to dataset images folder
            dst_img = dataset_dir / 'images' / split / src_path.name
            if not dst_img.exists():
                dst_img.write_bytes(src_path.read_bytes())

            # Run prediction
            results = model.predict(source=str(src_path), conf=0.25, verbose=False)
            # results is a list (one per image). We used single image so take first
            detections = []
            if results and len(results) > 0:
                res = results[0]
                boxes = getattr(res, 'boxes', None)
                if boxes is not None:
                    for box in boxes:
                        try:
                            xyxy = box.xyxy[0].tolist()
                            cls = int(box.cls[0])
                        except Exception:
                            # Fallback for different ultralytics versions
                            xyxy = box.xyxy.tolist()
                            cls = int(box.cls)

                        if cls in COCO_TO_LABEL:
                            label_id = COCO_TO_LABEL[cls]
                            x1, y1, x2, y2 = xyxy
                            xc, yc, bw, bh = xyxy_to_yolo(x1, y1, x2, y2, w, h)
                            detections.append((label_id, xc, yc, bw, bh))

            # Save label file
            label_path = dataset_dir / 'labels' / split / (src_path.stem + '.txt')
            save_label_file(label_path, detections)

    print("Processing train images...")
    process_list(train_imgs, 'train')
    if val_imgs:
        print("Processing val images...")
        process_list(val_imgs, 'val')

    # Write data.yaml
    data_yaml = dataset_dir / 'data.yaml'
    data_yaml.write_text(
        """
nc: %d
names: %s
train: %s
val: %s
""" % (
            len(LABEL_NAMES),
            LABEL_NAMES,
            str((dataset_dir / 'images' / 'train').as_posix()),
            str((dataset_dir / 'images' / 'val').as_posix()),
        )
    )

    print("Auto-labeling complete. Dataset created at:", dataset_dir)
    print("Label classes:", LABEL_NAMES)


if __name__ == '__main__':
    main()
