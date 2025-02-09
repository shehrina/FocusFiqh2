from pylsl import StreamInlet, resolve_streams
import time

# Thresholds based on your actual values
PROSTRATING_THRESHOLD = 0.017  # When fully down in sujood
BOWING_THRESHOLD = 0.028      # When bowing in ruku
STANDING_THRESHOLD = 0.033    # When standing
SITTING_THRESHOLD = 0.043     # When sitting

def detect_position(y_value):
    if y_value >= SITTING_THRESHOLD:
        return "Sitting"
    elif y_value >= STANDING_THRESHOLD:
        return "Standing"
    elif y_value >= BOWING_THRESHOLD:
        return "Bowing (Ruku)"
    elif y_value >= PROSTRATING_THRESHOLD:
        return "Prostrating (Sujood)"
    else:
        return "Transitioning"

print("Looking for all available LSL streams...")
streams = resolve_streams()

if not streams:
    print("❌ No LSL streams found.")
    exit()

# Connect to accelerometer stream
acc_streams = [s for s in streams if s.type() == 'ACC']
if not acc_streams:
    print("❌ No Accelerometer streams found.")
    exit()

inlet = StreamInlet(acc_streams[0])
print("✅ Connected to Accelerometer stream!")
print("\nStarting position detection...\n")

previous_position = None
last_change_time = time.time()
MIN_TIME_BETWEEN_CHANGES = 0.3  # Minimum time between position changes

while True:
    try:
        sample, _ = inlet.pull_sample(timeout=0.0)
        if sample:
            y_value = sample[1]
            current_position = detect_position(y_value)
            
            # Only update if position changed and enough time has passed
            current_time = time.time()
            if (current_position != previous_position and 
                current_time - last_change_time >= MIN_TIME_BETWEEN_CHANGES):
                print(f"Position: {current_position} (Y: {y_value:.4f})")
                previous_position = current_position
                last_change_time = current_time
        
        time.sleep(0.01)  # Small delay to prevent CPU overload
        
    except KeyboardInterrupt:
        print("\nStopping...")
        break