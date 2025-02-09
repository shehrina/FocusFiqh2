# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import time
import csv
from collections import deque

app = Flask(__name__)
CORS(app)

# Global settings and variables
sfreq = 256.0
buffer_size = int(sfreq)
eeg_buffer = deque(maxlen=buffer_size)

try:
    df = pd.read_csv("newprayer.csv")
except Exception as e:
    print(f"Error loading CSV: {e}")
    df = None

if df is None or not all(col in df.columns for col in ['TP9', 'AF7', 'AF8', 'TP10']):
    raise ValueError("CSV file must exist and contain columns: TP9, AF7, AF8, TP10")

eeg_data = df[['TP9', 'AF7', 'AF8', 'TP10']].values
num_samples = eeg_data.shape[0]
current_index = 0
demo_active = False

freq_bands = {
    'delta': (0.5, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta':  (13, 30),
    'gamma': (30, 70)
}

band_weights = {
    'alpha': 0.6,
    'theta': 0.3,
    'beta': -0.2,
    'delta': 0.1,
    'gamma': 0.0
}

def calculate_band_powers(eeg_buffer_data):
    data = np.array(eeg_buffer_data)
    fft_data = np.fft.fft(data, axis=0)
    freqs = np.fft.fftfreq(len(data), 1/sfreq)
    powers = {}
    for band, (low, high) in freq_bands.items():
        mask = (freqs >= low) & (freqs <= high)
        if np.sum(mask) == 0:
            powers[band] = 0
        else:
            band_fft = fft_data[mask]
            power = np.mean(np.abs(band_fft))
            powers[band] = float(power)
    return powers

def calculate_khushu_percentage(powers):
    total_power = sum(powers.values())
    if total_power == 0:
        return 0
    normalized_powers = {band: power/total_power for band, power in powers.items()}
    score = sum(band_weights[band] * normalized_powers[band] for band in freq_bands.keys())
    khushu_percentage = max(0, min(100, (score + 0.5) * 100))
    return khushu_percentage

@app.route('/start_demo', methods=['POST'])
def start_demo():
    global demo_active, current_index, eeg_buffer
    demo_active = True
    current_index = 0
    eeg_buffer.clear()
    return jsonify({"status": "Demo started"}), 200

@app.route('/end_demo', methods=['POST'])
def end_demo():
    global demo_active
    demo_active = False
    return jsonify({"status": "Demo ended"}), 200

@app.route('/data', methods=['GET'])
def get_data():
    global current_index, eeg_buffer, eeg_data, num_samples, demo_active
    if not demo_active:
        return jsonify({"status": "Demo not active"}), 200
    if current_index >= num_samples:
        current_index = 0
    sample = eeg_data[current_index]
    current_index += 1
    eeg_buffer.append(sample)
    current_time = current_index / sfreq
    raw_sample = {
        "TP9": float(sample[0]),
        "AF7": float(sample[1]),
        "AF8": float(sample[2]),
        "TP10": float(sample[3])
    }
    response = {
        "time": current_time,
        "raw_sample": raw_sample,
    }
    if len(eeg_buffer) == buffer_size:
        powers = calculate_band_powers(eeg_buffer)
        khushu_percentage = calculate_khushu_percentage(powers)
        theta_power = powers.get('theta', 1e-6)
        alpha_power = powers.get('alpha', 0)
        alpha_theta_ratio = alpha_power / theta_power if theta_power != 0 else 0
        response.update({
            "status": "processing",
            "band_powers": powers,
            "khushu_percentage": khushu_percentage,
            "alpha_theta_ratio": alpha_theta_ratio
        })
    else:
        response.update({
            "status": "buffering",
            "message": "Collecting initial data..."
        })
    return jsonify(response), 200

# New endpoint to save CSV file
@app.route('/save_csv', methods=['POST'])
def save_csv():
    data = request.get_json()  # Expect an array of objects
    if not data or not isinstance(data, list) or len(data) == 0:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    filename = "khushu_data.csv"
    try:
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return jsonify({"status": "CSV saved", "filename": filename}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)