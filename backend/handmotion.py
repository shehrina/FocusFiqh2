from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from collections import deque
import json
import os
import time
import threading
import sys
from select import select
import socket

app = Flask(__name__)
CORS(app)

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

class PrayerPositionDetector:
    def __init__(self):
        self.current_position = "transitioning"
        self.position_buffer = deque(maxlen=5)
        
        # Fixed thresholds based on your calibration data
        self.thresholds = {
            "standing": {
                "pitch": (-1.334, -1.298),
                "roll": (-179.706, -179.659)
            },
            "bowing": {
                "pitch": (-1.336, -1.276),
                "roll": (-179.667, -179.637)
            },
            "prostrating": {
                "pitch": (-1.293, -1.268),
                "roll": (-179.690, -179.667)
            },
            "sitting": {
                "pitch": (-1.336, -1.305),
                "roll": (-179.710, -179.664)
            }
        }
        
    def detect_position(self, pitch, roll):
        # Check each position against thresholds
        for position, ranges in self.thresholds.items():
            if (ranges["pitch"][0] <= pitch <= ranges["pitch"][1] and
                ranges["roll"][0] <= roll <= ranges["roll"][1]):
                self.position_buffer.append(position)
                break
        else:
            self.position_buffer.append("transitioning")
        
        # Calculate confidence
        if len(self.position_buffer) >= 3:
            positions = list(self.position_buffer)
            most_common = max(set(positions), key=positions.count)
            confidence = (positions.count(most_common) / len(positions)) * 100
            
            # Only update position if confidence > 60%
            if confidence > 60:
                self.current_position = most_common
                return {"position": most_common, "confidence": confidence}
            
        return {"position": "transitioning", "confidence": 0}

detector = PrayerPositionDetector()

def wait_for_enter():
    """Wait for Enter key without using keyboard library"""
    input()

def calibration_thread():
    positions = ["standing", "bowing", "prostrating", "sitting"]
    print("\nCalibration Mode Started!")
    
    for position in positions:
        print(f"\nPress Enter to start calibrating {position.upper()}...")
        wait_for_enter()
    
    print("\nCalibration Complete! Now detecting positions in real-time...")

@app.route('/data', methods=['GET', 'POST', 'OPTIONS'])
def data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if 'payload' in data:
                for measurement in data['payload']:
                    if measurement.get('name') == 'gravity':
                        values = measurement.get('values', {})
                        pitch = values.get('pitch', 0)
                        roll = values.get('roll', 0)
                        
                        result = detector.detect_position(pitch, roll)
                        
                        # Only print if confidence > 60%
                        if result["confidence"] > 60:
                            print(f"\rPosition: {result['position'].upper()} "
                                  f"(Confidence: {result['confidence']:.1f}%) "
                                  f"Pitch: {pitch:.1f}° Roll: {roll:.1f}°", end='')
                        
                        return jsonify({"status": "success", "result": result}), 200
            
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    ip_address = get_ip()
    print(f"""
Prayer Position Detection Server
==============================
SERVER URL: http://{ip_address}:3000/data

Using pre-calibrated values for:
- Standing
- Bowing (Rukuh)
- Prostrating (Sujood)
- Sitting

Only showing positions with >60% confidence
""")
    
    app.run(host='0.0.0.0', port=3000)