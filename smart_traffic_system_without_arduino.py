import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time
from pathlib import Path
# import serial  # Disabled for running without Arduino



class SmartTrafficManagementSystem:
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.3):
        """
        Initialize the Smart Traffic Management System with vehicle detection
        This version prioritizes lanes with more vehicles
        """
       

        print("Loading YOLO model...")
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold

        # Arduino communication disabled - running without hardware
        # self.arduino = serial.Serial('COM9', 9600)
        # time.sleep(2)
        self.arduino = None  # Set to None to indicate no Arduino connection
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
        }
        
        # Traffic signal colors
        self.GREEN_SIGNAL = (0, 255, 0)
        self.RED_SIGNAL = (0, 0, 255)
        self.YELLOW_SIGNAL = (0, 255, 255)
        
        # Timing for signals (in seconds, will be converted to frames)
        self.yellow_duration_sec = 5  # 5 seconds for yellow
        self.fps = 30  # Will be updated from video
        
    def detect_vehicles_in_frame(self, frame):
        """
        Detect vehicles in a single frame
        Returns vehicle count and annotated frame
        """
        if frame is None:
            return 0, frame, {}
        
        # Run YOLO detection
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        vehicle_counts = defaultdict(int)
        total_vehicles = 0
        
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
        
        return total_vehicles, frame, dict(vehicle_counts)
    
    def calculate_green_duration(self, vehicle_count, fps):
        """
        Calculate green signal duration based on vehicle count
        Less than 10: 15 seconds
        20-25: 25 seconds
        More than 30: 30 seconds
        Returns duration in frames
        """
        if vehicle_count < 10:
            duration_sec = 11
        elif 20 <= vehicle_count <= 30:
            duration_sec = 21
        elif vehicle_count > 30:
            duration_sec = 31
        else:
            # Between 10 and 20: scale between 15 and 25 seconds
            duration_sec = 15 + ((vehicle_count - 10) / 10) * 10
        
        return int(duration_sec * fps)
    
    def draw_traffic_signal(self, frame, signal_state, lane_name, vehicle_count, vehicle_breakdown, priority=False):
        """
        Draw traffic signal and vehicle count on frame
        """
        height, width = frame.shape[:2]
        
        # Draw semi-transparent overlay at the top
        overlay = frame.copy()
        overlay_height = 140
        cv2.rectangle(overlay, (0, 0), (width, overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw lane name with priority indicator
        lane_text = f"{lane_name}"
        if priority:
            lane_text += " [PRIORITY]"
            color = (0, 255, 255)  # Yellow for priority
        else:
            color = (255, 255, 255)
        
        cv2.putText(
            frame,
            lane_text,
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            color,
            3,
            cv2.LINE_AA
        )
        
        # Draw vehicle count with icon
        cv2.putText(
            frame,
            f"Total Vehicles: {vehicle_count}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
        
        # Draw vehicle breakdown
        y_pos = 100
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
        
        # Draw traffic signal (larger, more prominent)
        signal_center = (width - 70, 60)
        signal_radius = 45
        
        # Draw signal background with shadow
        cv2.circle(frame, (signal_center[0]+3, signal_center[1]+3), signal_radius + 5, (30, 30, 30), -1)
        cv2.circle(frame, signal_center, signal_radius + 5, (100, 100, 100), -1)
        
        # Draw signal color
        if signal_state == 'GREEN':
            color = self.GREEN_SIGNAL
            text = "GO"
        elif signal_state == 'YELLOW':
            color = self.YELLOW_SIGNAL
            text = "WAIT"
        else:  # RED
            color = self.RED_SIGNAL
            text = "STOP"
        
        cv2.circle(frame, signal_center, signal_radius, color, -1)
        cv2.circle(frame, signal_center, signal_radius, (255, 255, 255), 3)
        
        # Draw signal text
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = signal_center[0] - text_size[0] // 2
        text_y = signal_center[1] + text_size[1] // 2
        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            3,
            cv2.LINE_AA
        )
        
        return frame
    
    def signal_lane_change(self, lane):
        """
        Signal lane change for traffic light control
        If Arduino is connected, sends command; otherwise logs virtual signal
        lane: 0-based lane index
        """
        if lane < 0:
            return
        
        # Arduino communication disabled - virtual signal only
        if self.arduino is None:
            print(f"🚦 Virtual Signal: Lane {lane+1} GREEN")
            return
        
        # Send green signal command to Arduino (only if hardware is connected)
        cmd = f"L{lane+1}_G\n"
        self.arduino.write(cmd.encode())
        print(f"🚦 Arduino: Lane {lane+1} GREEN")

    def run_smart_traffic_system(self, video_paths):
        """
        Run the smart traffic management system with priority-based signal control
        First green light goes to lane with most vehicles, then alternates
        """
        # Open video captures
        caps = []
        for video_path in video_paths:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            caps.append(cap)
        
        # Get video properties and screen size
        fps = int(caps[0].get(cv2.CAP_PROP_FPS))
        self.fps = fps
        
        # Get screen resolution and calculate perfect fit
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        
        # Use 90% of screen for better fit, account for taskbar
        usable_height = int(screen_height * 0.90)
        usable_width = int(screen_width * 0.95)
        
        # Calculate dimensions for 2x2 grid
        frame_width = usable_width // 2
        frame_height = usable_height // 2
        
        # Calculate output video size (2x2 grid - 4 quarters)
        output_width = frame_width * 2
        output_height = frame_height * 2
        
        # Store current frame for each lane (for pause functionality)
        current_frames = [None] * len(caps)
        
        print(f"\nProcessing videos in PRIORITY mode...")
        print(f"Display: {output_width}x{output_height} @ {fps} FPS")
        print(f"Layout: 2x2 Grid (Perfect Screen Fit)")
        print(f"Green Light Timing: <10 cars=15s | 20-25 cars=25s | >30 cars=30s")
        
        frame_count = 0
        active_lane = -1  # Will be set based on priority
        
        green_duration_sec = 0  # Duration in seconds
        yellow_duration_sec = self.yellow_duration_sec
        first_cycle = True
        
        # Time tracking for real-time countdown
        signal_start_time = time.time()
        
        num_lanes = len(caps)
        lane_names = [f"LANE {i+1}" for i in range(num_lanes)]
        vehicle_counts = [0] * num_lanes
        vehicle_history = [[] for _ in range(num_lanes)]  # Track vehicle counts over time
        
        while True:
            frames = []
            
            # Always read frames from all videos to keep them playing in loop
            for i, cap in enumerate(caps):
                # Determine signal state for this lane
                is_active = (i == active_lane)
                
                # Calculate elapsed time for real-time countdown
                elapsed_time = time.time() - signal_start_time
                has_green_signal = is_active and elapsed_time < green_duration_sec
                
                # Always read new frame to keep video playing in loop
                ret, frame = cap.read()
                if not ret:
                    # Loop video back to start
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
                
                # Resize frame
                if frame is not None:
                    frame = cv2.resize(frame, (frame_width, frame_height))
                
                # Cache frame for pause effect on non-active lanes
                if has_green_signal:
                    current_frames[i] = frame
                else:
                    # RED signal - use cached frame (pause effect)
                    if current_frames[i] is not None:
                        frame = current_frames[i]
                    else:
                        current_frames[i] = frame
                
                frames.append(frame)
            
            # Process each lane
            processed_frames = []
            current_vehicle_counts = []
            
            for i, frame in enumerate(frames):
                # Determine signal state and priority FIRST
                priority = (i == active_lane)
                
                # Calculate elapsed time
                elapsed_time = time.time() - signal_start_time
                
                if i == active_lane:
                    # Show yellow in the last 5 seconds
                    if elapsed_time < (green_duration_sec - yellow_duration_sec):
                        signal_state = 'GREEN'
                    elif elapsed_time < green_duration_sec:
                        signal_state = 'YELLOW'
                    else:
                        signal_state = 'YELLOW'
                else:
                    signal_state = 'RED'
                
                # ONLY DETECT VEHICLES WHEN SIGNAL IS RED (before turning green)
                # Stop detection when signal is GREEN or YELLOW
                if signal_state == 'RED':
                    # Detect vehicles only for lanes with RED signal
                    vehicle_count, annotated_frame, vehicle_breakdown = self.detect_vehicles_in_frame(frame.copy())
                    vehicle_counts[i] = vehicle_count
                    current_vehicle_counts.append(vehicle_count)
                    vehicle_history[i].append(vehicle_count)
                    
                    # Keep only last 30 readings for average
                    if len(vehicle_history[i]) > 30:
                        vehicle_history[i].pop(0)
                else:
                    # GREEN or YELLOW signal - stop detection, use cached frame and last count
                    annotated_frame = frame.copy()
                    vehicle_count = vehicle_counts[i]  # Use last known count
                    current_vehicle_counts.append(vehicle_count)
                    vehicle_breakdown = {}  # No new breakdown
                
                # Draw annotations
                annotated_frame = self.draw_traffic_signal(
                    annotated_frame,
                    signal_state,
                    lane_names[i],
                    vehicle_count,
                    vehicle_breakdown,
                    priority
                )
                
                # Add green light timing for active lane - near the signal
                if i == active_lane and green_duration_sec > 0:
                    elapsed_time = time.time() - signal_start_time
                    remaining_time = max(0, int(green_duration_sec - elapsed_time))
                    total_time = int(green_duration_sec)
                    timing_text = f"{remaining_time}s"
                    
                    # Position timing near the signal (below the signal)
                    signal_x = frame_width - 70  # Same x as signal
                    signal_y = 60 + 60  # Below the signal
                    
                    # Draw timing background
                    (tw, th), _ = cv2.getTextSize(timing_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
                    cv2.rectangle(annotated_frame, 
                                (signal_x - tw//2 - 10, signal_y - th - 10), 
                                (signal_x + tw//2 + 10, signal_y + 10), 
                                (0, 0, 0), -1)
                    
                    # Draw timing text in green
                    cv2.putText(
                        annotated_frame,
                        timing_text,
                        (signal_x - tw//2, signal_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 255, 0),
                        3,
                        cv2.LINE_AA
                    )
                
                processed_frames.append(annotated_frame)
            
            # Combine frames in 2x2 grid layout
            if len(processed_frames) >= 4:
                # Top row: Lane 1 and Lane 2
                top_row = np.hstack([processed_frames[0], processed_frames[1]])
                # Bottom row: Lane 3 and Lane 4
                bottom_row = np.hstack([processed_frames[2], processed_frames[3]])
                combined_frame = np.vstack([top_row, bottom_row])
            elif len(processed_frames) == 3:
                # Handle 3 lanes: top row with 2, bottom row with 1 centered
                top_row = np.hstack([processed_frames[0], processed_frames[1]])
                bottom_row = np.hstack([processed_frames[2], np.zeros((frame_height, frame_width, 3), dtype=np.uint8)])
                combined_frame = np.vstack([top_row, bottom_row])
            elif len(processed_frames) == 2:
                # Handle 2 lanes: one row
                combined_frame = np.hstack(processed_frames)
            else:
                combined_frame = processed_frames[0] if processed_frames else np.zeros((output_height, output_width, 3), dtype=np.uint8)
            
            # Add system info at bottom
            avg_counts = [sum(hist)/len(hist) if hist else 0 for hist in vehicle_history]
            vehicle_info = " | ".join([f"L{i+1}={vehicle_counts[i]}" for i in range(len(vehicle_counts))])
            
            if active_lane >= 0:
                info_text = f"PRIORITY MODE | Active: {lane_names[active_lane]} ({int(green_duration_sec)}s) | Frame: {frame_count} | Vehicles: {vehicle_info}"
            else:
                info_text = f"PRIORITY MODE | Initializing... | Frame: {frame_count} | Vehicles: {vehicle_info}"
            
            cv2.rectangle(combined_frame, (0, output_height - 50), (output_width, output_height), (0, 0, 0), -1)
            cv2.putText(
                combined_frame,
                info_text,
                (10, output_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )
            
            # Display fullscreen fit
            cv2.namedWindow('Smart Traffic Management System [PRIORITY MODE] - Press Q to quit', cv2.WINDOW_NORMAL)
            cv2.imshow('Smart Traffic Management System [PRIORITY MODE] - Press Q to quit', combined_frame)
            
            # Calculate elapsed time for signal switching
            elapsed_time = time.time() - signal_start_time
            
            # First cycle: set active lane based on priority (most vehicles)
            if first_cycle and frame_count > 30:  # Wait 30 frames to collect data
                active_lane = avg_counts.index(max(avg_counts))
                green_duration_sec = self.calculate_green_duration(int(avg_counts[active_lane]), fps) / fps
                first_cycle = False
                signal_start_time = time.time()  # Reset timer
                self.signal_lane_change(active_lane)  # Signal lane change
                print(f"\n>>> First green light: {lane_names[active_lane]} with {int(avg_counts[active_lane])} vehicles ({int(green_duration_sec)}s green + {int(yellow_duration_sec)}s yellow)")
            
            # Switch lanes after green duration (yellow is included in the last 5 seconds)
            if active_lane >= 0 and elapsed_time >= green_duration_sec:
                # Alternate to next lane in sequence (priority-based rotation)
                active_lane = (active_lane + 1) % len(caps)
                
                # Calculate green duration based on vehicle count
                green_duration_sec = self.calculate_green_duration(int(avg_counts[active_lane]), fps) / fps
                
                # Reset timer for new signal cycle
                signal_start_time = time.time()
                
                # Signal lane change for new lane
                self.signal_lane_change(active_lane)
                
                print(f"\n>>> Switching to {lane_names[active_lane]} - {int(avg_counts[active_lane])} vehicles - {int(green_duration_sec)}s (last 5s yellow)")
            
            frame_count += 1
            
            if frame_count % 30 == 0 and active_lane >= 0:
                print(f"Processed {frame_count} frames | Active: {lane_names[active_lane]} | Counts: {vehicle_counts}")
            
            # Wait for normal playback speed (1000ms / fps)
            if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
                print("\nStopped by user")
                break
        
        # Cleanup
        for cap in caps:
            cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n✓ Complete! Processed {frame_count} frames")


def main():
    """
    Main function - runs traffic system in priority mode with looping videos
    """
    video_dir = Path("traffic video")
    
    # Check for 4 lane videos first, fallback to 3 if not available
    video_paths = []
    for i in range(1, 5):
        video_path = video_dir / f"lane {i}.mp4"
        if video_path.exists():
            video_paths.append(video_path)
    
    # If less than 3 videos, try the original 3
    if len(video_paths) < 3:
        video_paths = [
            video_dir / "lane 1.mp4",
            video_dir / "lane 2.mp4",
            video_dir / "lane 3.mp4"
        ]
    
    # Check videos
    for video_path in video_paths:
        if not video_path.exists():
            print(f"Error: Video not found: {video_path}")
            return
    
    print("=" * 80)
    print("SMART AI TRAFFIC MANAGEMENT SYSTEM - PRIORITY MODE")
    print("=" * 80)
    print(f"\n✓ Detected {len(video_paths)} lane(s)")
    print(f"✓ Display: 2x2 Grid Layout (Perfect Screen Fit)")
    print(f"✓ Mode: PRIORITY-BASED with alternating green signals")
    print(f"✓ Behavior: RED signal = DETECT & PAUSE, GREEN signal = PLAY & NO DETECTION")
    print(f"✓ Videos: Continuous loop until stopped")
    print(f"✓ Detection: Only active on RED signal lanes (before green light)")
    print(f"\nGreen Light Timing:")
    print(f"  • Less than 10 vehicles → 15 seconds")
    print(f"  • 20-25 vehicles → 25 seconds")
    print(f"  • More than 30 vehicles → 30 seconds")
    print(f"\nFirst green light goes to lane with most vehicles")
    print(f"\nPress 'Q' to stop the system")
    print("=" * 80)
    print("\n🚦 Starting system...\n")
    
    # Create system
    tms = SmartTrafficManagementSystem(
        model_name='yolov8n.pt',
        confidence_threshold=0.3
    )
    
    # Run in priority mode
    tms.run_smart_traffic_system(video_paths=video_paths)
    
    print("\n" + "=" * 70)
    print("SYSTEM COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
