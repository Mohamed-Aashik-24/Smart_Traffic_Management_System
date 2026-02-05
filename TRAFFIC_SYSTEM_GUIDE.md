# AI Traffic Management System - User Guide

## Overview
This system processes 3 traffic lane videos simultaneously, detects vehicles using YOLOv8, and manages traffic signals automatically.

## Features
- ✅ Real-time vehicle detection in 3 lanes
- ✅ Automatic traffic signal management (Green/Yellow/Red)
- ✅ Vehicle counting and classification (cars, trucks, buses, motorcycles, bicycles)
- ✅ Annotated video output with bounding boxes
- ✅ All 3 lanes displayed side-by-side
- ✅ Automatic lane rotation (each lane gets green signal in turns)

## How It Works

1. **Vehicle Detection**: YOLOv8 model detects vehicles in each frame of all 3 videos
2. **Signal Management**: 
   - One lane gets GREEN signal at a time
   - Other 2 lanes get RED signal
   - GREEN duration: ~5 seconds
   - YELLOW duration: ~1 second (transition)
   - Lanes rotate automatically
3. **Annotation**: Each detected vehicle is marked with:
   - Bounding box (color-coded by vehicle type)
   - Vehicle type and confidence score
   - Traffic signal status
   - Vehicle count

## Usage

### Run the system:
```bash
python traffic_management_system.py
```

### What you'll see:
- Live display window showing all 3 lanes side-by-side
- Each lane shows:
  - Lane name (LANE 1, LANE 2, LANE 3)
  - Vehicle count
  - Vehicle breakdown by type
  - Traffic signal (Green/Yellow/Red circle)
- Bottom bar shows system statistics
- Press 'Q' to stop

### Output:
- Annotated video saved as: `traffic_output_annotated.mp4`
- Contains all 3 lanes processed together
- Can be played with any video player

## Color Coding

### Vehicles:
- 🟢 Green: Cars
- 🔴 Red: Motorcycles
- 🔵 Blue: Buses
- 🟠 Orange: Trucks
- 🟡 Cyan: Bicycles

### Traffic Signals:
- 🟢 GREEN: Lane is active, vehicles can go
- 🟡 YELLOW: Transition, prepare to stop
- 🔴 RED: Lane is stopped, wait

## Configuration

You can adjust settings in the code:

```python
# In TrafficManagementSystem class:
self.green_duration = 150  # frames (~5 seconds at 30 fps)
self.yellow_duration = 30  # frames (~1 second)
self.confidence_threshold = 0.3  # Detection confidence (0.0 to 1.0)
```

## Requirements
- Python 3.8+
- YOLOv8 model (yolov8n.pt)
- 3 video files in "traffic video" folder:
  - lane 1.mp4
  - lane 2.mp4
  - lane 3.mp4

## Tips
- Videos will loop automatically if they end
- System processes videos in real-time
- Lower confidence_threshold for more detections
- Higher confidence_threshold for more accurate detections
- Adjust green_duration for longer/shorter signal times

## Troubleshooting

**Issue**: Video not found
- **Solution**: Check that videos are in "traffic video" folder

**Issue**: Slow processing
- **Solution**: Use a smaller YOLO model (yolov8n.pt is fastest)

**Issue**: Too many/few detections
- **Solution**: Adjust confidence_threshold (default: 0.3)

**Issue**: Display window too large
- **Solution**: Window is automatically resized to 1920x540

## System Flow
```
Start → Load 3 Videos → Process Frame from Each Video →
Detect Vehicles → Update Signal States → Annotate Frames →
Combine 3 Frames Side-by-Side → Display & Save →
Rotate to Next Lane → Repeat
```

Enjoy your AI Traffic Management System! 🚦🚗
