import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import os
import sys
import argparse
from pathlib import Path


class VehicleDetector:
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.3):
        """
        Initialize the Vehicle Detector
        """
        print("Loading YOLO model...")
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold

        # COCO dataset class IDs for vehicles
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck',
            1: 'bicycle'
        }

        # Colors for different vehicle types (BGR format)
        self.colors = {
            'car': (0, 255, 0),        # Green
            'motorcycle': (0, 0, 255),  # Red
            'bus': (255, 0, 0),         # Blue
            'truck': (0, 165, 255),     # Orange
            'bicycle': (255, 255, 0),   # Cyan
            'ambulance': (0, 255, 255)  # Yellow
        }

    def detect_vehicles(self, image_path):
        """
        Detect vehicles in an image
        Returns annotated image and a dict of vehicle counts
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image from {image_path}")

        # Run YOLO detection
        print("Running detection...")
        results = self.model(image, conf=self.confidence_threshold)

        vehicle_counts = defaultdict(int)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                except Exception:
                    continue

                if class_id in self.vehicle_classes:
                    vehicle_type = self.vehicle_classes[class_id]
                    vehicle_counts[vehicle_type] += 1
                    color = self.colors.get(vehicle_type, (255, 255, 255))

                    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                    label = f"{vehicle_type}: {confidence:.2f}"
                    (label_width, label_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                    )
                    cv2.rectangle(
                        image,
                        (x1, y1 - label_height - 10),
                        (x1 + label_width, y1),
                        color,
                        -1
                    )
                    cv2.putText(
                        image,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

        # Add count overlay
        self._add_count_overlay(image, vehicle_counts)
        return image, dict(vehicle_counts)

    def _add_count_overlay(self, image, vehicle_counts):
        overlay_height = 50 + len(vehicle_counts) * 30
        overlay_width = 300
        overlay = image.copy()
        cv2.rectangle(overlay, (10, 10), (overlay_width, overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        cv2.putText(image, "Vehicle Count Summary", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
                    cv2.LINE_AA)

        y_offset = 65
        total_vehicles = 0
        for vehicle_type, count in sorted(vehicle_counts.items()):
            color = self.colors.get(vehicle_type, (255, 255, 255))
            text = f"{vehicle_type.capitalize()}: {count}"
            cv2.putText(image, text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
            y_offset += 30
            total_vehicles += count

        cv2.putText(image, f"Total: {total_vehicles}", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255), 2, cv2.LINE_AA)

    def save_result(self, image, output_path):
        cv2.imwrite(output_path, image)
        print(f"Result saved to: {output_path}")

    def display_result(self, image, window_name="Vehicle Detection"):
        max_height = 800
        height, width = image.shape[:2]
        if height > max_height:
            scale = max_height / height
            new_width = int(width * scale)
            image = cv2.resize(image, (new_width, max_height))
        cv2.imshow(window_name, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description='Detect vehicles in images inside a folder and display them one-by-one')
    parser.add_argument('--folder', '-f', type=str, default='Traffic vehicle',
                        help='Path to folder containing images')
    parser.add_argument('--model', '-m', type=str, default='yolov8s.pt',
                        help='YOLO model file to use (default: yolov8s.pt)')
    parser.add_argument('--conf', type=float, default=0.3, help='Confidence threshold for detections')
    parser.add_argument('--out', type=str, default='outputs', help='Output folder for annotated images')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    folder_path = Path(args.folder)
    if not folder_path.is_absolute():
        folder_path = (script_dir / folder_path).resolve()

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Input folder not found: {folder_path}")
        sys.exit(1)

    detector = VehicleDetector(model_name=args.model, confidence_threshold=args.conf)

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = (script_dir / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.avif', '.tif', '.tiff'}
    images = [p for p in sorted(folder_path.iterdir()) if p.suffix.lower() in exts]

    if not images:
        print(f"No image files found in {folder_path}")
        sys.exit(0)

    for img_path in images:
        try:
            print('\n' + '=' * 60)
            print(f"Processing: {img_path.name}")
            annotated_image, vehicle_counts = detector.detect_vehicles(str(img_path))
            total = sum(vehicle_counts.values())
            print(f"Results for {img_path.name} -> Total vehicles: {total}")
            if vehicle_counts:
                for vt, c in sorted(vehicle_counts.items()):
                    print(f"  {vt.capitalize()}: {c}")
            else:
                print("  No vehicles detected.")

            out_file = out_dir / f"detected_{img_path.name}"
            detector.save_result(annotated_image, str(out_file))
            detector.display_result(annotated_image, window_name=f"Detection - {img_path.name}")

        except Exception as e:
            print(f"Error processing {img_path.name}: {e}")

    print('\nAll images processed. Annotated images saved to: ' + str(out_dir))


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()