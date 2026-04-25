# 👁️ Real-Time Blink & Drowsiness Detection

---

## Overview

This project detects blinks and drowsiness in real time using a webcam. It uses dlib's facial landmark predictor to track eye movements and calculates the Eye Aspect Ratio (EAR) to determine whether the eyes are open or closed. When prolonged eye closure is detected, an audio alarm is triggered to alert the user. The system auto-calibrates on startup to adapt to different hardware speeds and lighting conditions using histogram equalization.

---

## Requirements

- Python 3.x
- [dlib](http://dlib.net/)
- OpenCV (`cv2`)
- scipy
- numpy
- playsound

Install dependencies:

```bash
pip install dlib opencv-python scipy numpy playsound
```

---

## Setup

1. Download the shape predictor model:
   - [`shape_predictor_70_face_landmarks.dat`](http://dlib.net/files/)
   - Place it inside a `models/` folder in the project root.

2. Add an alarm sound file:
   - Place `alarm.wav` in the project root.

---

## Usage

```bash
python blinkDetect.py
```

- The program will **auto-calibrate** for 100 frames before starting detection.
- Press **`r`** to reset drowsiness state.
- Press **`Esc`** to quit.

---

## Author

**Rithikaa**

If you found this project helpful or interesting, consider giving it a ⭐ — it means a lot and helps others discover it!
