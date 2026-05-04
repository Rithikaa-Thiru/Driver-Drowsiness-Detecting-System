from datetime import datetime
import threading
import time
import cv2
from flask import Flask, jsonify, request
from flask_cors import CORS
import mediapipe as mp
import numpy as np
import pywhatkit as kit
import sounddevice as sd
import pyautogui

# ==============================
# GLOBAL PHONE NUMBER
# ==============================
PHONE = "+916374005413"

def set_phone_number(number):
    global PHONE
    PHONE = number
    print("📱 Updated phone:", PHONE)

# ==============================
# WHATSAPP (FIXED)
# ==============================
def send_whatsapp():
    try:
        message = "🚨 Drowsiness Detected! Stay alert!"

        kit.sendwhatmsg_instantly(
            PHONE,
            message,
            wait_time=10,
            tab_close=False
        )

        print("⌛ Waiting WhatsApp Web...")
        time.sleep(5)   # optional delay before send

        pyautogui.press("enter")

        print("📲 WhatsApp SENT to", PHONE)

    except Exception as e:
        print("❌ WhatsApp error:", e)

# ==============================
# FLASK SERVER
# ==============================
app = Flask(__name__)
CORS(app)

alerts = []

@app.route("/set_number", methods=["POST"])
def set_number():
    data = request.json
    number = data.get("phone")

    if number:
        set_phone_number(number)
        return jsonify({"status": "ok", "phone": PHONE})

    return jsonify({"status": "error", "message": "No number provided"})

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>SafeDrive Monitor</title>
<style>
body { font-family: Arial; background:#0f172a; color:white; text-align:center;}
h1 { color:#00ffcc; }
input, button { padding:10px; margin:5px; }
.alert-box {
    background:#1e293b;
    margin:10px auto;
    padding:15px;
    width:60%;
    border-left:5px solid red;
}
</style>
</head>

<body>

<h1>🚗 SafeDrive Monitor</h1>

<input id="phone" placeholder="Enter WhatsApp Number (+91...)" />
<button onclick="setNumber()">Set Number</button>

<div id="status">Connecting...</div>
<div id="alerts"></div>

<script>
async function setNumber(){
    let phone = document.getElementById("phone").value;

    let res = await fetch("/set_number", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({phone})
    });

    let data = await res.json();
    alert("Number updated: " + data.phone);
}

async function fetchAlerts(){
    let res = await fetch("/alerts");
    let data = await res.json();

    document.getElementById("status").innerText = "✅ Connected";

    let box = document.getElementById("alerts");
    box.innerHTML = "";

    if(data.length === 0){
        box.innerHTML = "<p>No alerts yet</p>";
        return;
    }

    data.slice().reverse().forEach(a=>{
        box.innerHTML += `
        <div class="alert-box">
            <b>${a.alert}</b><br>${a.time}
        </div>`;
    });
}

setInterval(fetchAlerts, 2000);
fetchAlerts();
</script>

</body>
</html>
"""

@app.route("/alerts")
def get_alerts():
    return jsonify(alerts)

def run_server():
    print("🌐 Open: http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)

# ==============================
# SOUND ALERT
# ==============================
def play_alarm():
    try:
        fs = 44100
        duration = 1.5

        t = np.linspace(0, duration, int(fs * duration), False)
        tone = 0.5 * np.sin(2 * np.pi * 1000 * t)

        sd.play(tone, fs)
        sd.wait()

        print("🔊 Alarm played")

    except Exception as e:
        print("❌ Sound error:", e)

# ==============================
# DETECTION (5 SECOND FIX)
# ==============================
def run_detection():
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

    LEFT_EYE = [33,160,158,133,153,144]
    RIGHT_EYE = [362,385,387,263,373,380]

    EAR_THRESHOLD = 0.22
    DROWSY_TIME = 5   # 🔥 5 SECONDS FIX

    blink_count = 0
    closed_frames = 0
    BLINK_FRAMES = 3

    eye_was_closed = False
    eye_closed_start = None
    alarm_on = False

    def calculate_EAR(eye):
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        return 0 if C == 0 else (A + B) / (2 * C)

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        ear = 0.0

        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                h, w, _ = frame.shape

                left_eye = []
                right_eye = []

                for i in LEFT_EYE:
                    left_eye.append([int(face.landmark[i].x*w),
                                     int(face.landmark[i].y*h)])

                for i in RIGHT_EYE:
                    right_eye.append([int(face.landmark[i].x*w),
                                      int(face.landmark[i].y*h)])

                left_eye = np.array(left_eye)
                right_eye = np.array(right_eye)

                ear = (calculate_EAR(left_eye) + calculate_EAR(right_eye)) / 2

                # ==========================
                # BLINK DETECTION
                # ==========================
                if ear < EAR_THRESHOLD:
                    closed_frames += 1
                else:
                    if closed_frames >= BLINK_FRAMES:
                        blink_count += 1

                    closed_frames = 0

                    eye_was_closed = False
                    eye_closed_start = None
                    alarm_on = False

                # ==========================
                # DROWSINESS (5 SECONDS)
                # ==========================
                if ear < EAR_THRESHOLD:
                    if not eye_was_closed:
                        eye_closed_start = time.time()
                        eye_was_closed = True

                    else:
                        duration = time.time() - eye_closed_start

                        if duration >= DROWSY_TIME:
                            if not alarm_on:
                                alerts.append({
                                    "alert": "Drowsiness Detected (5s closure)",
                                    "time": time.strftime("%H:%M:%S")
                                })

                                play_alarm()
                                send_whatsapp()
                                alarm_on = True

        # UI DISPLAY
        cv2.putText(frame, f"EAR: {ear:.2f}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)

        cv2.putText(frame, f"Blinks: {blink_count}", (15, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.imshow("SafeDrive", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    run_detection()