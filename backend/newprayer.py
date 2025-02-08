import pandas as pd
import numpy as np
import mne
import matplotlib.pyplot as plt

# 1) Load the CSV file:
df = pd.read_csv("newprayer.csv")

#   Adjust if your CSV has different columns. Typically, muselsl outputs:
#   ['timestamps','TP9','AF7','AF8','TP10','Right AUX']
#   We'll assume you have these exact columns. If your AUX is named differently,
#   update the code below accordingly.

# 2) Convert columns (ignoring 'timestamps') into a NumPy array, shape = (n_channels, n_times)
data = df[["TP9","AF7","AF8","TP10","Right AUX"]].to_numpy().T

# 3) Create MNE Info object
#    Muse 2 typically streams at 256 Hz. Adjust if needed.
sfreq = 256.0
ch_names = ["TP9","AF7","AF8","TP10","RightAUX"]
ch_types = ["eeg","eeg","eeg","eeg","eeg"]

info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

# 4) Build the MNE Raw object
raw = mne.io.RawArray(data, info)

# 5) Save to FIF (optional)
raw.save("muse_data_raw.fif", overwrite=True)

# 6) Plot in an interactive window
#    'block=True' keeps the window open until you close it
raw.plot(block=True)

# If needed, also do plt.show() to explicitly force a matplotlib window
plt.show()
