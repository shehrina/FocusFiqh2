import time
import numpy as np
from pylsl import StreamInlet, resolve_byprop
from scipy.signal import welch

# ✅ STEP 1: RESOLVE MUSE STREAMS
print("Resolving Muse LSL streams...")

# Connect to EEG stream
eeg_streams = resolve_byprop('type', 'EEG', timeout=10)
inlet_eeg = StreamInlet(eeg_streams[0]) if eeg_streams else None
print("✅ Connected to EEG stream!")

# Connect to PPG (heart rate) stream
ppg_streams = resolve_byprop('type', 'PPG', timeout=10)
inlet_ppg = StreamInlet(ppg_streams[0]) if ppg_streams else None
print("✅ Connected to PPG stream!")

# Connect to Accelerometer stream
acc_streams = resolve_byprop('type', 'ACC', timeout=10)
inlet_acc = StreamInlet(acc_streams[0]) if acc_streams else None
print("✅ Connected to Accelerometer stream!")

# ✅ STEP 2: ARTICLE REFERENCE VALUES
ARTICLE_REFERENCES = {
    "standing":    {"alpha": 28.38, "hr": 75},
    "bowing":      {"alpha": 28.38, "hr": 75},
    "prostration": {"alpha": 28.38, "hr": 75},
    "sitting":     {"alpha": 28.38, "hr": 75}
}

# ✅ STEP 3: ACCUMULATE EEG SAMPLES TO AVOID nperseg ERROR
eeg_buffer = []  # Stores EEG samples

def compute_alpha_relative_power(eeg_sample, fs=256):
    """
    Store EEG samples in a buffer and compute alpha relative power when enough data is collected.
    """
    global eeg_buffer
    eeg_buffer.append(eeg_sample)  # Add new sample

    if len(eeg_buffer) < 256:  # Wait until we have at least 256 samples
        return None  # Not enough data yet

    # Convert buffer to NumPy array and keep only the last 256 samples
    eeg_data = np.array(eeg_buffer[-256:])
    
    # Compute alpha power
    freqs, psd = welch(eeg_data, fs=fs, nperseg=256)
    alpha_mask = (freqs >= 8) & (freqs <= 13)
    total_mask = (freqs >= 1) & (freqs <= 40)

    total_power = np.trapz(psd[total_mask], freqs[total_mask])
    alpha_power = np.trapz(psd[alpha_mask], freqs[alpha_mask])

    return alpha_power / total_power if total_power > 0 else 0

# ✅ STEP 4: PROCESS HEART RATE FROM PPG
def compute_heart_rate(ppg_data):
    """
    Compute the average heart rate (BPM) from PPG data.
    """
    return np.mean(ppg_data)  # Assuming ppg_data contains BPM estimates

# ✅ STEP 5: DETECT POSTURE USING ACCELEROMETER
def detect_posture(acc_data):
    """
    Estimate posture based on accelerometer X, Y, Z values.
    """
    acc_x, acc_y, acc_z = acc_data
    pitch_angle = np.degrees(np.arctan2(acc_y, acc_z))  # Compute pitch

    if -10 <= pitch_angle <= 10:
        return "standing"
    elif 40 <= pitch_angle <= 90:
        return "bowing"
    elif 90 <= pitch_angle <= 120:
        return "prostration"
    elif 60 <= pitch_angle <= 80:
        return "sitting"
    else:
        return "transition"

# ✅ STEP 6: COMPUTE KHUSHŪ’ %
def compute_khushu_percent(posture, alpha_current, hr_current):
    """
    Compute Khushū’ percentage for a given posture.
    """
    alpha_ref = ARTICLE_REFERENCES[posture]["alpha"]
    hr_ref = ARTICLE_REFERENCES[posture]["hr"]

    alpha_ratio = alpha_current / alpha_ref
    hr_ratio = hr_ref / hr_current

    return 100 * alpha_ratio * hr_ratio

# ✅ STEP 7: REAL-TIME DATA PROCESSING
def main_loop():
    print("\n🚀 Starting real-time Khushū’ calculation...\n")
    current_posture = None

    while True:
        # Read EEG sample
        eeg_sample, _ = inlet_eeg.pull_sample(timeout=0.1) if inlet_eeg else (None, None)
        alpha_rel = compute_alpha_relative_power(eeg_sample) if eeg_sample else None

        if alpha_rel is None:  # Wait until we have enough EEG data
            continue

        # Read PPG (Heart Rate)
        ppg_sample, _ = inlet_ppg.pull_sample(timeout=0.1) if inlet_ppg else (None, None)
        hr = compute_heart_rate([ppg_sample[0]]) if ppg_sample else None

        # Read Accelerometer
        acc_sample, _ = inlet_acc.pull_sample(timeout=0.1) if inlet_acc else (None, None)
        posture = detect_posture(acc_sample) if acc_sample else None

        if posture and hr:
            if posture != current_posture:  # Detect posture change
                current_posture = posture
                khushu_percent = compute_khushu_percent(posture, alpha_rel, hr)
                print(f"{posture.upper()}: {khushu_percent:.2f}% Khushū’")

        time.sleep(0.5)

# Run real-time processing
main_loop()
