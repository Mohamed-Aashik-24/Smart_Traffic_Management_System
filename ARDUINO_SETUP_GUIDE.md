from arduino_controller import ArduinoTrafficController

# Connect to COM9 manually
controller = ArduinoTrafficController(port='COM9')

if controller.is_connected:
    print("✅ Connected!")
    controller.set_red()
    input("Press Enter to test yellow...")
    controller.set_yellow()
    input("Press Enter to test green...")
    controller.set_green()
    controller.close()# Arduino Traffic Signal Setup Guide - Lane 2

## Hardware Requirements

### Components Needed:
1. **Arduino Uno** (1x)
2. **LEDs** (3x):
   - Red LED (1x)
   - Yellow/Amber LED (1x)
   - Green LED (1x)
3. **Resistors** (3x 220Ω or 330Ω)
4. **Breadboard** (1x)
5. **Jumper Wires** (male-to-male)
6. **USB Cable** (Type A to Type B for Arduino Uno)

## Circuit Setup

### Wiring Diagram:

```
Arduino Pin 13 ──► [220Ω Resistor] ──► Red LED (+) ──► GND (-)
Arduino Pin 12 ──► [220Ω Resistor] ──► Yellow LED (+) ──► GND (-)
Arduino Pin 11 ──► [220Ω Resistor] ──► Green LED (+) ──► GND (-)
```

### Step-by-Step Wiring:

1. **Red LED (STOP Signal)**
   - Connect Pin 13 to a 220Ω resistor
   - Connect resistor to the **positive leg** (longer leg) of Red LED
   - Connect **negative leg** (shorter leg) to GND rail on breadboard

2. **Yellow LED (WAIT Signal)**
   - Connect Pin 12 to a 220Ω resistor
   - Connect resistor to the **positive leg** of Yellow LED
   - Connect **negative leg** to GND rail on breadboard

3. **Green LED (GO Signal)**
   - Connect Pin 11 to a 220Ω resistor
   - Connect resistor to the **positive leg** of Green LED
   - Connect **negative leg** to GND rail on breadboard

4. **Ground Connection**
   - Connect Arduino GND to the breadboard GND rail

### Visual Layout:
```
      Arduino Uno
    ┌─────────────┐
    │             │
    │   13 ●──────┼──[220Ω]──►(🔴 RED LED)──►GND
    │             │
    │   12 ●──────┼──[220Ω]──►(🟡 YELLOW LED)──►GND
    │             │
    │   11 ●──────┼──[220Ω]──►(🟢 GREEN LED)──►GND
    │             │
    │  GND ●──────┼─────────────►GND Rail
    │             │
    └─────────────┘
```

## Software Setup

### Step 1: Upload Arduino Code

1. **Install Arduino IDE**
   - Download from: https://www.arduino.cc/en/software
   - Install and open Arduino IDE

2. **Open the Arduino sketch**
   - Open `traffic_signal_arduino.ino` in Arduino IDE

3. **Select Board & Port**
   - Tools → Board → Arduino Uno
   - Tools → Port → Select the COM port (e.g., COM3, COM4)
   
4. **Upload Code**
   - Click the **Upload** button (→ arrow icon)
   - Wait for "Done uploading" message

5. **Test with Serial Monitor**
   - Open Tools → Serial Monitor
   - Set baud rate to **9600**
   - Type commands:
     - `R` = Red LED
     - `Y` = Yellow LED (blinking)
     - `G` = Green LED

### Step 2: Install Python Dependencies

```powershell
pip install pyserial
```

### Step 3: Test Arduino Connection

Run the test script to verify everything works:

```powershell
python arduino_controller.py
```

This will cycle through all signals:
- 🔴 RED (3 seconds)
- 🟡 YELLOW blinking (5 seconds)
- 🟢 GREEN (3 seconds)

## Integration with Traffic System

### Option 1: Standalone Test

Test the Arduino controller independently:

```python
from arduino_controller import ArduinoTrafficController
import time

# Create controller
controller = ArduinoTrafficController()

# Control signals manually
controller.set_red()
time.sleep(5)

controller.set_yellow()
time.sleep(3)

controller.set_green()
time.sleep(10)

controller.close()
```

### Option 2: Integrate with Smart Traffic System

Modify your main traffic system to send signals to Arduino:

```python
from arduino_controller import ArduinoTrafficController

# In your SmartTrafficManagementSystem class
class SmartTrafficManagementSystem:
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.3):
        # ... existing code ...
        
        # Add Arduino controller for Lane 2
        self.arduino_controller = ArduinoTrafficController()
    
    def update_lane_signal(self, lane_index, signal_state):
        """Update Arduino signal for Lane 2"""
        if lane_index == 1 and self.arduino_controller.is_connected:  # Lane 2 (index 1)
            if signal_state == 'RED':
                self.arduino_controller.set_red()
            elif signal_state == 'YELLOW':
                self.arduino_controller.set_yellow()
            elif signal_state == 'GREEN':
                self.arduino_controller.set_green()
```

## Troubleshooting

### Arduino Not Detected

**Problem:** Python can't find the Arduino

**Solutions:**
1. Check USB connection
2. Install CH340 drivers (for clone Arduino boards)
   - Download: http://www.wch.cn/downloads/CH341SER_ZIP.html
3. Check Device Manager (Windows) for COM port
4. Try different USB cable
5. Specify port manually:
   ```python
   controller = ArduinoTrafficController(port='COM3')
   ```

### LEDs Not Lighting Up

**Problem:** LEDs don't turn on

**Solutions:**
1. Check LED polarity (longer leg = positive)
2. Verify resistor connections
3. Test LED with multimeter
4. Check if code uploaded successfully
5. Test with Serial Monitor commands (R, Y, G)

### Serial Port Already in Use

**Problem:** "Access denied" or "Port already open"

**Solutions:**
1. Close Arduino IDE Serial Monitor
2. Close other programs using the port
3. Unplug and replug Arduino
4. Restart computer if needed

### LEDs Too Dim or Too Bright

**Problem:** LED brightness issues

**Solutions:**
- Too dim: Use smaller resistor (150Ω)
- Too bright: Use larger resistor (330Ω or 470Ω)
- Formula: R = (Vcc - Vled) / I
  - For 5V Arduino: R = (5 - 2) / 0.02 = 150Ω minimum

## Signal States

| State  | LED    | Duration | Arduino Command |
|--------|--------|----------|-----------------|
| STOP   | 🔴 Red | Variable | `R` |
| WAIT   | 🟡 Yellow (Blinking) | 5 seconds | `Y` |
| GO     | 🟢 Green | Variable | `G` |

## Serial Communication Protocol

- **Baud Rate:** 9600
- **Commands:** Single character (R, Y, G)
- **Response:** Confirmation message
- **Example:**
  ```
  Send: G
  Receive: Signal changed to: GREEN (GO)
  ```

## Safety Notes

⚠️ **Important:**
- Don't exceed 20mA per LED
- Always use current-limiting resistors
- Connect LEDs with correct polarity
- Don't short-circuit Arduino pins
- Unplug Arduino when wiring

## Next Steps

1. ✅ Wire up the circuit on breadboard
2. ✅ Upload Arduino code
3. ✅ Test with `arduino_controller.py`
4. ✅ Integrate with main traffic system
5. 🎯 Monitor Lane 2 signals in real-time!

---

**Need Help?** Check the code comments in:
- `traffic_signal_arduino.ino` - Arduino control logic
- `arduino_controller.py` - Python serial communication
