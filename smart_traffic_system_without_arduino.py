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
            duration_sec = 6
        elif 20 <= vehicle_count <= 30:
            duration_sec = 11
        elif vehicle_count > 30:
            duration_sec = 16
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
        Run the smart traffic management system with a sliding 4-lane window.

        With N videos (e.g. 5), exactly 4 are displayed at a time in a 2x2 grid.
        After every full 4-lane cycle, the window slides by 1:
          Round 1 → Lanes 1-2-3-4
          Round 2 → Lanes 2-3-4-5
          Round 3 → Lanes 3-4-5-1  ... and so on.

        First green light goes to the lane with the most vehicles (priority).
        Subsequent lanes rotate sequentially within the current window.
        """
        WINDOW_SIZE = 4  # always display this many lanes

        # --- Open ALL video captures ---
        all_caps = []
        for video_path in video_paths:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            all_caps.append(cap)

        num_total = len(all_caps)
        if num_total < WINDOW_SIZE:
            raise ValueError(f"Need at least {WINDOW_SIZE} videos, got {num_total}")

        # --- Video / screen properties ---
        fps = int(all_caps[0].get(cv2.CAP_PROP_FPS)) or 30
        self.fps = fps

        import tkinter as tk
        root = tk.Tk()
        screen_width  = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()

        usable_height = int(screen_height * 0.90)
        usable_width  = int(screen_width  * 0.95)
        frame_width   = usable_width  // 2
        frame_height  = usable_height // 2
        output_width  = frame_width  * 2
        output_height = frame_height * 2

        print(f"\nProcessing {num_total} videos — displaying {WINDOW_SIZE} at a time (sliding window)")
        print(f"Display: {output_width}x{output_height} @ {fps} FPS  |  Layout: 2×2 Grid")
        print(f"Round 1: L1-L2-L3-L4  →  Round 2: L2-L3-L4-L5  →  Round 3: L3-L4-L5-L1 ...")

        lane_names = [f"LANE {i+1}" for i in range(num_total)]

        # --- Per-cap tracking (indexed by absolute cap index 0..num_total-1) ---
        current_frames  = [None] * num_total   # cached frame for pause effect
        vehicle_counts  = [0]    * num_total
        vehicle_history = [[]    for _ in range(num_total)]

        # --- Sliding-window state ---
        window_start    = 0   # which cap index is first in the visible 4
        window_cycle    = 0   # greens given so far in this window (1-4)
        window_round    = 1   # display round counter

        # --- Signal state ---
        frame_count        = 0
        active_win_idx     = -1   # index 0-3 within visible window; -1 = not yet started
        green_duration_sec = 0
        yellow_duration_sec = self.yellow_duration_sec
        first_cycle        = True
        signal_start_time  = time.time()

        # =====================================================================
        while True:
            # Current visible 4 cap indices
            visible   = [(window_start + i) % num_total for i in range(WINDOW_SIZE)]
            win_label = " ".join([f"L{visible[i]+1}" for i in range(WINDOW_SIZE)])

            elapsed_time = time.time() - signal_start_time

            # -----------------------------------------------------------------
            # 1. Read & cache frames for the 4 visible lanes
            # -----------------------------------------------------------------
            raw_frames = []  # list of (win_pos, cap_idx, frame)
            for win_pos, cap_idx in enumerate(visible):
                cap      = all_caps[cap_idx]
                is_active = (win_pos == active_win_idx)
                has_green = is_active and elapsed_time < green_duration_sec

                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

                if frame is not None:
                    frame = cv2.resize(frame, (frame_width, frame_height))

                if has_green:
                    current_frames[cap_idx] = frame          # update cache while green
                else:
                    # RED/YELLOW — use cached (pause effect)
                    if current_frames[cap_idx] is not None:
                        frame = current_frames[cap_idx]
                    else:
                        current_frames[cap_idx] = frame      # first frame ever

                raw_frames.append((win_pos, cap_idx, frame))

            # -----------------------------------------------------------------
            # 2. Detect vehicles & annotate
            # -----------------------------------------------------------------
            processed_frames = []
            for win_pos, cap_idx, frame in raw_frames:
                is_active    = (win_pos == active_win_idx)
                elapsed_time = time.time() - signal_start_time

                if is_active:
                    remaining = green_duration_sec - elapsed_time
                    signal_state = 'GREEN' if remaining > yellow_duration_sec else 'YELLOW'
                else:
                    signal_state = 'RED'

                if signal_state == 'RED':
                    vc, annotated, vb = self.detect_vehicles_in_frame(frame.copy())
                    vehicle_counts[cap_idx] = vc
                    vehicle_history[cap_idx].append(vc)
                    if len(vehicle_history[cap_idx]) > 30:
                        vehicle_history[cap_idx].pop(0)
                else:
                    annotated = frame.copy()
                    vc = vehicle_counts[cap_idx]
                    vb = {}

                annotated = self.draw_traffic_signal(
                    annotated, signal_state,
                    lane_names[cap_idx], vc, vb, is_active
                )

                # Countdown timer for the active lane
                if is_active and green_duration_sec > 0:
                    elapsed_time    = time.time() - signal_start_time
                    remaining_time  = max(0, int(green_duration_sec - elapsed_time))
                    timing_text     = f"{remaining_time}s"
                    signal_x        = frame_width - 70
                    signal_y        = 60 + 60
                    (tw, th), _     = cv2.getTextSize(timing_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
                    cv2.rectangle(annotated,
                                  (signal_x - tw//2 - 10, signal_y - th - 10),
                                  (signal_x + tw//2 + 10, signal_y + 10),
                                  (0, 0, 0), -1)
                    cv2.putText(annotated, timing_text,
                                (signal_x - tw//2, signal_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)

                processed_frames.append(annotated)

            # -----------------------------------------------------------------
            # 3. Build 2×2 grid
            # -----------------------------------------------------------------
            top_row    = np.hstack([processed_frames[0], processed_frames[1]])
            bottom_row = np.hstack([processed_frames[2], processed_frames[3]])
            combined_frame = np.vstack([top_row, bottom_row])

            # -----------------------------------------------------------------
            # 4. Info bar at bottom
            # -----------------------------------------------------------------
            veh_info = " | ".join(
                [f"L{cap_idx+1}={vehicle_counts[cap_idx]}" for _, cap_idx, _ in raw_frames]
            )
            if active_win_idx >= 0:
                act_cap   = visible[active_win_idx]
                info_text = (f"Round {window_round} | Window:[{win_label}] | "
                             f"Active:{lane_names[act_cap]}({int(green_duration_sec)}s) | {veh_info}")
            else:
                info_text = (f"Round {window_round} | Window:[{win_label}] | "
                             f"Initializing... | {veh_info}")

            cv2.rectangle(combined_frame,
                          (0, output_height - 50), (output_width, output_height),
                          (0, 0, 0), -1)
            cv2.putText(combined_frame, info_text, (10, output_height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.namedWindow('Smart Traffic Management System [PRIORITY MODE] - Press Q to quit',
                            cv2.WINDOW_NORMAL)
            cv2.imshow('Smart Traffic Management System [PRIORITY MODE] - Press Q to quit',
                       combined_frame)

            # -----------------------------------------------------------------
            # 5. Signal logic
            # -----------------------------------------------------------------
            elapsed_time = time.time() - signal_start_time

            # --- First cycle: pick priority lane from the visible 4 ---
            if first_cycle and frame_count > 30:
                avg_counts = [
                    sum(vehicle_history[visible[i]]) / len(vehicle_history[visible[i]])
                    if vehicle_history[visible[i]] else 0
                    for i in range(WINDOW_SIZE)
                ]
                active_win_idx     = avg_counts.index(max(avg_counts))
                green_duration_sec = self.calculate_green_duration(
                    int(avg_counts[active_win_idx]), fps) / fps
                window_cycle       = 1          # this lane counts as the 1st in the window
                first_cycle        = False
                signal_start_time  = time.time()
                # Signal uses window position (0-3) as physical lane — video rotates, hardware stays L1-L4
                self.signal_lane_change(active_win_idx)
                print(f"\n>>> Round {window_round} | Window:[{win_label}] | "
                      f"First green → {lane_names[visible[active_win_idx]]} (Signal L{active_win_idx+1}) "
                      f"({int(avg_counts[active_win_idx])} vehicles, {int(green_duration_sec)}s)")

            # --- Switch lanes after green+yellow expires ---
            if active_win_idx >= 0 and elapsed_time >= green_duration_sec:

                if window_cycle >= WINDOW_SIZE:
                    # ---- All 4 lanes in this window have had a turn → slide window ----
                    window_start   = (window_start + 1) % num_total
                    window_round  += 1
                    window_cycle   = 0
                    active_win_idx = 0          # start from the first lane of the new window
                    visible        = [(window_start + i) % num_total for i in range(WINDOW_SIZE)]
                    win_label      = " ".join([f"L{visible[i]+1}" for i in range(WINDOW_SIZE)])
                    print(f"\n>>> Window shifted → Round {window_round} | New Window:[{win_label}]")
                else:
                    # ---- Move to next lane within the same window ----
                    active_win_idx = (active_win_idx + 1) % WINDOW_SIZE

                window_cycle += 1   # count the newly-activated lane

                avg_counts = [
                    sum(vehicle_history[visible[i]]) / len(vehicle_history[visible[i]])
                    if vehicle_history[visible[i]] else 0
                    for i in range(WINDOW_SIZE)
                ]
                green_duration_sec = self.calculate_green_duration(
                    int(avg_counts[active_win_idx]), fps) / fps
                signal_start_time  = time.time()
                # Signal uses window position (0-3) as physical lane — video rotates, hardware stays L1-L4
                self.signal_lane_change(active_win_idx)
                print(f"\n>>> Round {window_round} | Window:[{win_label}] | "
                      f"→ {lane_names[visible[active_win_idx]]} (Signal L{active_win_idx+1}) "
                      f"({int(avg_counts[active_win_idx])} vehicles, {int(green_duration_sec)}s)")

            frame_count += 1

            if frame_count % 30 == 0 and active_win_idx >= 0:
                print(f"Frame {frame_count} | Window:[{win_label}] | "
                      f"Active:{lane_names[visible[active_win_idx]]} | "
                      f"Counts:{[vehicle_counts[visible[i]] for i in range(WINDOW_SIZE)]}")

            if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
                print("\nStopped by user")
                break

        # Cleanup
        for cap in all_caps:
            cap.release()
        cv2.destroyAllWindows()
        print(f"\n✓ Complete! Processed {frame_count} frames")


def main():
    """
    Main function - runs traffic system with a sliding 4-lane window.

    Loads up to 5 lane videos (lane 1.mp4 … lane 5.mp4).
    Always shows exactly 4 lanes at a time in a 2x2 grid.
    After every full 4-lane cycle the window shifts by 1:
        Round 1: L1-L2-L3-L4
        Round 2: L2-L3-L4-L5
        Round 3: L3-L4-L5-L1
        Round 4: L4-L5-L1-L2
        Round 5: L5-L1-L2-L3  ... and repeats.
    """
    video_dir = Path("traffic video")

    # Collect all available lane videos (lane 1.mp4 … lane 5.mp4)
    video_paths = []
    for i in range(1, 6):
        video_path = video_dir / f"lane {i}.mp4"
        if video_path.exists():
            video_paths.append(video_path)

    if len(video_paths) < 4:
        print(f"Error: Need at least 4 lane videos. Found only {len(video_paths)}:")
        for p in video_paths:
            print(f"  ✓ {p}")
        for i in range(1, 6):
            p = video_dir / f"lane {i}.mp4"
            if not p.exists():
                print(f"  ✗ {p}  ← missing")
        return

    print("=" * 80)
    print("SMART AI TRAFFIC MANAGEMENT SYSTEM - SLIDING WINDOW MODE")
    print("=" * 80)
    print(f"\n✓ Detected {len(video_paths)} lane video(s):")
    for p in video_paths:
        print(f"    {p.name}")
    print(f"\n✓ Display : 2×2 Grid — always 4 lanes visible at a time")
    print(f"✓ Mode    : Priority-based first green, then sequential rotation")
    print(f"✓ Sliding : Window shifts by 1 lane after every full 4-lane cycle")
    print(f"✓ Behavior: RED = detect & pause | GREEN/YELLOW = play, no detection")
    print(f"\nGreen Light Timing:")
    print(f"  • < 10 vehicles  →  ~15 seconds")
    print(f"  • 20-30 vehicles →  ~25 seconds")
    print(f"  • > 30 vehicles  →  ~30 seconds")
    print(f"\nFirst green light goes to the lane with the most vehicles.")
    print(f"Press 'Q' to stop.")
    print("=" * 80)
    print("\n🚦 Starting system...\n")

    tms = SmartTrafficManagementSystem(
        model_name='yolov8n.pt',
        confidence_threshold=0.3
    )

    tms.run_smart_traffic_system(video_paths=video_paths)

    print("\n" + "=" * 70)
    print("SYSTEM COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
