from pylsl import StreamInlet, resolve_streams
import time

# Updated thresholds based on Y values progression
STANDING_THRESHOLD_Y = 0.033  # Y >= 0.033 (average ~0.0336)
BOWING_THRESHOLD_Y = 0.028    # Y >= 0.028 (average ~0.0283)
PROSTRATING_THRESHOLD_Y = 0.017  # Y around 0.017 (average ~0.0174)
SITTING_THRESHOLD_Y = 0.043    # Y >= 0.043 (average ~0.0436)

# Function to detect position based primarily on Y values
def detect_position(x, y, z):
    if y >= SITTING_THRESHOLD_Y:
        return "Sitting"
    elif y >= STANDING_THRESHOLD_Y:
        return "Standing"
    elif y >= BOWING_THRESHOLD_Y:
        return "Bowing (Ruku)"
    elif y >= PROSTRATING_THRESHOLD_Y:
        return "Prostrating (Sujood)"
    else:
        return "Transitioning"

print("Looking for all available LSL streams...")

# First, let's see all available streams
streams = resolve_streams()

if not streams:
    print("❌ No LSL streams found at all.")
    exit()

print("\nAvailable streams:")
for stream in streams:
    print(f"- Name: {stream.name()}")
    print(f"  Type: {stream.type()}")
    print(f"  Channel count: {stream.channel_count()}")
    print()

# Now try specifically for accelerometer
acc_streams = [s for s in streams if s.type() == 'ACC']

if not acc_streams:
    print("❌ No Accelerometer streams found. Available types are:")
    print([s.type() for s in streams])
    exit()

# Connect to the first available accelerometer stream
inlet = StreamInlet(acc_streams[0])
print("✅ Connected to Accelerometer stream!")

# Read data continuously
print("Starting live position detection...")
previous_position = None

while True:
    sample, timestamp = inlet.pull_sample()
    x, y, z = sample[0], sample[1], sample[2]
    
    # Detect position based on Y values
    current_position = detect_position(x, y, z)
    
    # Print the detected position in the desired format
    print(f"Time: {timestamp}, X: {x}, Y: {y}, Z: {z}, Position: {current_position}")
    
    # Wait for 2.5 seconds before the next update
    time.sleep(1)