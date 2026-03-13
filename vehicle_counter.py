import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time


class VehicleCounter:
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.5, enable_ambulance_detection=True):
        """
        Initialize Vehicle Counter with YOLO model
        """
        print("Loading YOLO model...")
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold
        self.enable_ambulance_detection = enable_ambulance_detection
        
        # COCO dataset class IDs for vehicles
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck',
            1: 'bicycle'
        }
        
        # Emergency vehicle detection (ambulance is typically detected as truck/bus)
        self.ambulance_classes = {5: 'bus', 7: 'truck'}  # Ambulances detected as bus/truck
        self.ambulance_conf_threshold = 0.55  # Threshold for ambulance detection
        self.ambulance_min_area = 6000   # Minimum pixel area (smaller for compact ambulances)
        self.ambulance_max_area = 30000  # Maximum pixel area (exclude large buses)
        
        # Colors for different vehicle types (BGR format)
        self.colors = {
            'car': (0, 255, 0),        # Green
            'motorcycle': (0, 0, 255),  # Red
            'bus': (255, 0, 0),         # Blue
            'truck': (0, 165, 255),     # Orange
            'bicycle': (255, 255, 0),   # Cyan
            'ambulance': (0, 0, 255),   # Red (Emergency)
        }
        
    def count_vehicles_in_frame(self, frame):
        """
        Count vehicles in a single frame including ambulances
        Returns total count, annotated frame, breakdown by vehicle type, and ambulance flag
        """
        if frame is None:
            return 0, frame, {}, False
        
        # Run YOLO detection
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        vehicle_counts = defaultdict(int)
        total_vehicles = 0
        ambulance_detected = False
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                except Exception:
                    continue
                
                # Check for ambulance (high confidence bus/truck with specific characteristics)
                is_ambulance = False
                if self.enable_ambulance_detection and class_id in self.ambulance_classes:
                    box_area = (x2 - x1) * (y2 - y1)
                    
                    if (confidence > self.ambulance_conf_threshold and 
                        self.ambulance_min_area < box_area < self.ambulance_max_area):
                        
                        # Extract vehicle region for color analysis
                        vehicle_region = frame[y1:y2, x1:x2]
                        if vehicle_region.size > 0:
                            hsv = cv2.cvtColor(vehicle_region, cv2.COLOR_BGR2HSV)
                            
                            # Check for white/light colors (common for ambulances)
                            lower_white = np.array([0, 0, 180])
                            upper_white = np.array([180, 50, 255])
                            white_mask = cv2.inRange(hsv, lower_white, upper_white)
                            white_ratio = np.count_nonzero(white_mask) / white_mask.size
                            
                            # Check for red colors (ambulance markings, lights)
                            lower_red1 = np.array([0, 100, 100])
                            upper_red1 = np.array([10, 255, 255])
                            lower_red2 = np.array([170, 100, 100])
                            upper_red2 = np.array([180, 255, 255])
                            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                            red_ratio = np.count_nonzero(red_mask) / red_mask.size
                            
                            # Detect as ambulance if:
                            # - More than 20% white/light (small ambulances often very white)
                            # - OR has red markings (>8% red pixels)
                            # - OR is a medium-sized vehicle with high confidence
                            if (white_ratio > 0.20 or 
                                red_ratio > 0.08 or 
                                (confidence > 0.65 and self.ambulance_min_area < box_area < self.ambulance_max_area)):
                                is_ambulance = True
                                ambulance_detected = True
                                vehicle_type = 'ambulance'
                                vehicle_counts['ambulance'] += 1
                                print(f"🚨 AMBULANCE DETECTED! Confidence: {confidence:.2f}, "
                                      f"Size: {box_area}, White: {white_ratio:.2%}, Red: {red_ratio:.2%}")
                
                if not is_ambulance and class_id in self.vehicle_classes:
                    vehicle_type = self.vehicle_classes[class_id]
                    vehicle_counts[vehicle_type] += 1
                    total_vehicles += 1
                    color = self.colors.get(vehicle_type, (255, 255, 255))
                    
                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    
                    # Draw label
                    label = f"{vehicle_type}: {confidence:.2f}"
                    (label_width, label_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                    )
                    cv2.rectangle(
                        frame,
                        (x1, y1 - label_height - 10),
                        (x1 + label_width, y1),
                        color,
                        -1
                    )
                    cv2.putText(
                        frame,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 0),
                        2,
                        cv2.LINE_AA,
                    )
                elif is_ambulance:
                    # Emergency vehicle - special rendering
                    total_vehicles += 1
                    color = self.colors['ambulance']
                    
                    # Draw thicker, flashing-style bounding box
                    thickness = 5
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                    
                    # Draw emergency label with warning
                    label = f"⚠️ AMBULANCE: {confidence:.2f} ⚠️"
                    (label_width, label_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                    )
                    # Draw red background
                    cv2.rectangle(
                        frame,
                        (x1, y1 - label_height - 15),
                        (x1 + label_width, y1),
                        (0, 0, 255),
                        -1
                    )
                    cv2.putText(
                        frame,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )
        
        return total_vehicles, frame, dict(vehicle_counts), ambulance_detected
    
    def draw_count_overlay(self, frame, total_count, vehicle_breakdown, ambulance_detected=False):
        """
        Draw vehicle count information on frame
        """
        height, width = frame.shape[:2]
        
        # Draw semi-transparent overlay at the top
        overlay = frame.copy()
        overlay_height = 120 + (len(vehicle_breakdown) * 25)
        if ambulance_detected:
            overlay_height += 40  # Extra space for ambulance alert
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw title
        cv2.putText(
            frame,
            "VEHICLE COUNTER",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
        
        # Draw ambulance alert if detected
        if ambulance_detected:
            cv2.putText(
                frame,
                "🚨 EMERGENCY: AMBULANCE DETECTED! 🚨",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )
            y_offset = 100
        else:
            y_offset = 65
        
        # Draw total count
        cv2.putText(
            frame,
            f"Total Vehicles: {total_count}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )
        
        # Draw vehicle breakdown
        y_pos = y_offset + 30
        for vtype, count in vehicle_breakdown.items():
            text = f"{vtype.capitalize()}: {count}"
            color = self.colors.get(vtype, (255, 255, 255))
            cv2.putText(
                frame,
                text,
                (10, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA
            )
            y_pos += 25
        
        return frame
    
    def count_from_camera(self, camera_index=0):
        """
        Count vehicles from camera feed (real-time)
        camera_index: 0 for default camera, 1 for external camera, etc.
        """
        print(f"\nOpening camera {camera_index}...")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return
        
        print("Camera opened successfully!")
        print("Press 'Q' to quit, 'S' to save screenshot")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Count vehicles
            total_count, annotated_frame, breakdown, ambulance_detected = self.count_vehicles_in_frame(frame.copy())
            
            # Draw overlay
            annotated_frame = self.draw_count_overlay(annotated_frame, total_count, breakdown, ambulance_detected)
            
            # Add FPS counter
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f}",
                (annotated_frame.shape[1] - 150, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )
            
            # Display
            cv2.imshow('Vehicle Counter - Camera Feed', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nStopped by user")
                break
            elif key == ord('s'):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"vehicle_count_{timestamp}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"Screenshot saved: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nTotal frames processed: {frame_count}")
        print(f"Average FPS: {fps:.2f}")
    
    def count_from_video(self, video_path):
        """
        Count vehicles from video file
        video_path: Path to video file
        """
        print(f"\nOpening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file: {video_path}")
            return
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video properties: {width}x{height} @ {fps} FPS, {total_frames} frames")
        print("Press 'Q' to quit, 'S' to save screenshot, 'SPACE' to pause")
        
        frame_count = 0
        paused = False
        max_count = 0
        max_count_frame = 0
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("\nEnd of video reached")
                    break
                
                # Count vehicles
                total_count, annotated_frame, breakdown, ambulance_detected = self.count_vehicles_in_frame(frame.copy())
                
                # Track maximum count
                if total_count > max_count:
                    max_count = total_count
                    max_count_frame = frame_count
                
                # Draw overlay
                annotated_frame = self.draw_count_overlay(annotated_frame, total_count, breakdown, ambulance_detected)
                
                # Add progress bar
                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                cv2.putText(
                    annotated_frame,
                    f"Progress: {progress:.1f}% | Frame: {frame_count}/{total_frames}",
                    (10, height - 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )
                
                cv2.putText(
                    annotated_frame,
                    f"Max count so far: {max_count} (frame {max_count_frame})",
                    (10, height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA
                )
                
                frame_count += 1
            
            # Display
            cv2.imshow('Vehicle Counter - Video', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(int(1000 / fps)) & 0xFF
            if key == ord('q'):
                print("\nStopped by user")
                break
            elif key == ord('s'):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"vehicle_count_{timestamp}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"Screenshot saved: {filename}")
            elif key == ord(' '):
                paused = not paused
                print("Paused" if paused else "Resumed")
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total frames processed: {frame_count}")
        print(f"Maximum vehicles detected: {max_count} (at frame {max_count_frame})")
        print(f"{'='*60}")


def main():
    """
    Main function - choose camera or video input
    """
    print("=" * 60)
    print("VEHICLE COUNTER")
    print("=" * 60)
    print("\nSelect input source:")
    print("1. Camera (real-time)")
    print("2. Video file")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    counter = VehicleCounter(
        model_name='yolov8n.pt',
        confidence_threshold=0.5
    )
    
    if choice == '1':
        camera_index = input("Enter camera index (0 for default, 1 for external): ").strip()
        try:
            camera_index = int(camera_index)
        except ValueError:
            camera_index = 0
        counter.count_from_camera(camera_index=camera_index)
    
    elif choice == '2':
        video_path = input("Enter video file path (or press Enter for default): ").strip()
        if not video_path:
            # Try default video from traffic video folder
            video_path = "traffic video/lane 1.mp4"
        counter.count_from_video(video_path=video_path)
    
    elif choice == '3':
        print("Exiting...")
        return
    
    else:
        print("Invalid choice!")
        return
    
    print("\nThank you for using Vehicle Counter!")


if __name__ == "__main__":
    main()
