# 🚦 Smart Traffic Management System

An AI-powered traffic management system that uses YOLOv8 for real-time vehicle detection and intelligent traffic signal control with Arduino integration.

## 📋 Overview

This system processes multiple traffic lane videos simultaneously, detects and counts vehicles using AI, and manages traffic signals automatically. It includes both software-only and hardware-integrated (Arduino) versions.

### ✨ Key Features

- 🚗 **Real-time Vehicle Detection** using YOLOv8 AI model
- 🚦 **Smart Traffic Signal Control** with priority-based and round-robin modes
- 📹 **Multi-lane Video Processing** (supports 3 lanes simultaneously)
- 🎨 **Visual Annotations** with bounding boxes and vehicle counts
- 🔌 **Arduino Integration** for physical traffic light control
- 📊 **Vehicle Classification** (cars, motorcycles, buses, trucks, bicycles)

## 📁 Project Structure

```
Smart Traffic Management System/
├── smart_traffic_system.py              # Advanced system with Arduino
├── smart_traffic_system_without_arduino.py  # Software-only version
├── traffic_signal.ino                   # Arduino firmware
├── requirements.txt                     # Python dependencies
├── yolov8n.pt / yolov8s.pt             # YOLOv8 model weights
├── COMPLETE_SYSTEM_OVERVIEW.md          # Detailed system documentation
├── ARDUINO_SETUP_GUIDE.md               # Hardware setup guide
├── traffic video/                       # Input video files
│   ├── lane 1.mp4
│   ├── lane 2.mp4
│   └── lane 3.mp4
└── output/                              # Generated output videos
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Arduino Uno (optional, for hardware integration)
- Webcam or video files for traffic lanes

### Installation

1. **Clone the repository**
```powershell
git clone https://github.com/Mohamed-Aashik-24/Smart_Traffic_Management_System.git
cd Smart_Traffic_Management_System
```

2. **Create virtual environment and install dependencies**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

### Running the System

#### Option 1: Software Only (No Arduino)
```powershell
python smart_traffic_system_without_arduino.py
```

#### Option 2: With Arduino Integration
```powershell
# First, upload traffic_signal.ino to your Arduino
# Then run:
python smart_traffic_system.py
```

## 🎯 How It Works

### Vehicle Detection
- Uses YOLOv8 model for real-time object detection
- Detects: cars, motorcycles, buses, trucks, bicycles
- Each vehicle type has unique color-coded bounding boxes
- Displays confidence scores for each detection

### Traffic Signal Management

**Two Operating Modes:**

1. **PRIORITY Mode** (Smart/Adaptive)
   - Analyzes vehicle count in each lane
   - Gives priority to lanes with more vehicles
   - Dynamic green signal duration based on traffic density
   - Optimizes traffic flow automatically

2. **ROTATE Mode** (Round-Robin)
   - Fixed time allocation for each lane
   - Sequential rotation through all lanes
   - Predictable signal timing

### Signal States
- 🟢 **GREEN** - Active lane, vehicles can pass
- 🟡 **YELLOW** - Transition phase (5 seconds)
- 🔴 **RED** - Inactive lanes, vehicles must stop

## ⚙️ Configuration

### Changing Mode
Edit in `smart_traffic_system.py`:
```python
mode = 'PRIORITY'  # or 'ROTATE'
```

### Adjusting Timing
```python
yellow_duration_sec = 5      # Yellow signal duration
min_green_duration_sec = 5   # Minimum green time
max_green_duration_sec = 15  # Maximum green time
```

### Arduino COM Port
```python
self.arduino = serial.Serial('COM9', 9600)  # Change COM9 to your port
```

## 🔧 Hardware Setup (Arduino)

### Required Components
- Arduino Uno (1x)
- LEDs: Red, Yellow, Green (1x each)
- Resistors: 220Ω (3x)
- Breadboard and jumper wires

### Wiring
```
Pin 13 → Red LED (through 220Ω resistor) → GND
Pin 12 → Yellow LED (through 220Ω resistor) → GND
Pin 11 → Green LED (through 220Ω resistor) → GND
```

See [ARDUINO_SETUP_GUIDE.md](ARDUINO_SETUP_GUIDE.md) for detailed instructions.

## 📊 Output

### Visual Display
- Side-by-side view of all lanes
- Real-time vehicle counts
- Bounding boxes with labels
- Current signal state for each lane

### Saved Files
- `traffic_output_priority.mp4` - Priority mode output
- `traffic_output_rotate.mp4` - Rotate mode output
- `traffic_output_annotated.mp4` - Basic system output

## 🛠️ Troubleshooting

### Common Issues

**Arduino not connecting:**
- Check COM port in Device Manager
- Update Arduino drivers
- Verify correct port in code

**Video not loading:**
- Check video files exist in `traffic video/` folder
- Verify video codec compatibility
- Ensure file names match: `lane 1.mp4`, `lane 2.mp4`, `lane 3.mp4`

**Low detection accuracy:**
- Use `yolov8s.pt` instead of `yolov8n.pt` for better accuracy
- Adjust `confidence_threshold` (default: 0.3)

## 📚 Documentation

- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - Comprehensive system guide
- [ARDUINO_SETUP_GUIDE.md](ARDUINO_SETUP_GUIDE.md) - Hardware setup instructions

## 🎨 Vehicle Types & Colors

| Vehicle Type | Bounding Box Color | Class ID |
|-------------|-------------------|----------|
| 🚗 Car      | Green            | 2        |
| 🏍️ Motorcycle | Red            | 3        |
| 🚌 Bus      | Blue             | 5        |
| 🚚 Truck    | Orange           | 7        |
| 🚲 Bicycle  | Cyan             | 1        |

## 🔑 Key Technologies

- **YOLOv8** - State-of-the-art object detection
- **OpenCV** - Computer vision and video processing
- **PySerial** - Arduino communication
- **NumPy** - Numerical operations
- **Ultralytics** - YOLO implementation

## 📝 Requirements

```
ultralytics>=8.0.0
opencv-python
numpy>=1.21.0
pathlib
pyserial (for Arduino integration)
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Author

**Mohamed Aashik**
- GitHub: [@Mohamed-Aashik-24](https://github.com/Mohamed-Aashik-24)

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- OpenCV community
- Arduino community

---

For detailed setup and usage instructions, please refer to the [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) file.
