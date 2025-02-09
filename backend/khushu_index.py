from pylsl import StreamInlet, resolve_streams
import time
import numpy as np
from statistics import mean, stdev
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import csv
import os

plt.style.use('dark_background')  # Better visibility
plt.ion()  # Enable interactive mode

class KhushuMonitor:
    def __init__(self):
        # Get the backend directory path
        self.backend_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set CSV paths in backend directory
        self.csv_filename = os.path.join(self.backend_dir, "khushu_results.csv")
        self.detailed_csv_filename = os.path.join(self.backend_dir, "detailed_session.csv")
        
        print("Looking for Muse EEG stream...")
        streams = resolve_streams()
        
        # Connect to EEG stream
        eeg_streams = [s for s in streams if s.type() == 'EEG']
        if not eeg_streams:
            raise RuntimeError("""
            No EEG stream found! Please check:
            1. Is your Muse turned on?
            2. Is it paired via Bluetooth?
            3. Is BlueMuse/MuseLSL running?
            4. Can you see the stream in BlueMuse/MuseLSL?
            """)
        
        # Create the inlet
        self.eeg_inlet = StreamInlet(eeg_streams[0])
        print("✅ Connected to EEG stream!")
        
        # Get the last test number from CSV FIRST
        try:
            if os.path.exists(self.csv_filename):
                with open(self.csv_filename, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # If there are any results
                        last_line = lines[-1]
                        # Extract just the number from "Test X"
                        last_test_num = int(last_line.split(',')[0].split()[-1])
                        self.test_number = last_test_num + 1
                    else:
                        self.test_number = 1
            else:
                self.test_number = 1
                # Create file with headers if it doesn't exist
                with open(self.csv_filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Test Number', 'Average Khushu Index'])
        except Exception as e:
            print(f"Warning: Could not read last test number: {e}")
            self.test_number = 1
            
        # Channel indices for Muse 2
        self.channels = {
            'TP9': 0,
            'AF7': 1,
            'AF8': 2,
            'TP10': 3
        }
        
        # Will be set during calibration
        self.alpha_baseline = None
        self.alpha_std = None
        
        # Define frequency bands (from the paper)
        self.freq_bands = {
            'delta': (0.5, 4),    # Deep sleep, unconscious processes
            'theta': (4, 8),      # Drowsiness, meditation
            'alpha': (8, 13),     # Relaxed focus, meditation
            'beta': (13, 30),     # Active thinking, focus
            'gamma': (30, 70)     # Higher cognitive processes
        }
        
        # Weights for khushu calculation based on research findings
        # Alpha is dominant in meditation states and correlates with calm focus
        # Theta is associated with deep meditation
        # High beta might indicate wandering thoughts
        self.band_weights = {
            'alpha': 0.6,  # Increased weight as paper shows alpha is key in meditation
            'theta': 0.3,  # Associated with meditation state
            'beta': -0.2,  # Reduced weight for active thinking
            'delta': 0.1,  # Some presence is normal
            'gamma': 0.0   # Not directly relevant for khushu
        }
        
        # Initialize data structures for plotting
        self.times = []
        self.band_values = {band: [] for band in self.freq_bands}
        self.khushu_values = []
        
        # Create figure and subplots
        self.setup_plots()
    
    def setup_plots(self):
        """Initialize the visualization"""
        self.fig = plt.figure(figsize=(12, 8))
        
        # Brain wave subplot
        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title('Brain Wave Activity', color='white')
        self.ax1.set_xlabel('Time (seconds)', color='white')
        self.ax1.set_ylabel('Relative Power (μV²)', color='white')
        self.ax1.grid(True, alpha=0.3)
        
        # Initialize lines for each frequency band
        self.wave_lines = {}
        colors = {'delta': 'blue', 'theta': 'cyan', 'alpha': 'green', 
                 'beta': 'yellow', 'gamma': 'red'}
        
        # Create a line for each band
        for band, color in colors.items():
            self.wave_lines[band], = self.ax1.plot([], [], 
                                                  color=color, 
                                                  linewidth=2, 
                                                  label=f'{band.title()} Band')
        self.ax1.legend(loc='upper right')
        
        # Khushu level subplot
        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_title('Khushu Level', color='white')
        self.ax2.set_xlabel('Time (seconds)', color='white')
        self.ax2.set_ylabel('Percentage (%)', color='white')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        
        # Initialize khushu line
        self.khushu_line, = self.ax2.plot([], [], 'g-', linewidth=2, label='Khushu Level')
        self.ax2.legend(loc='upper right')
        
        # Add text for feedback
        self.feedback_text = self.fig.text(0.02, 0.02, '', color='white')
        
        plt.tight_layout()
        self.fig.canvas.draw()
    
    def update_plots(self):
        """Update the plots with new data"""
        if len(self.times) > 1:
            # Update each wave line
            for band, line in self.wave_lines.items():
                line.set_data(self.times, self.band_values[band])
            
            # Update khushu line
            self.khushu_line.set_data(self.times, self.khushu_values)
            
            # Adjust axes
            self.ax1.relim()
            self.ax1.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
            self.ax2.set_ylim(0, 100)
            
            # Update display
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
    
    def calculate_band_powers(self, eeg_data):
        """Calculate power in each frequency band"""
        # Convert to numpy array
        data = np.array(eeg_data)
        
        # Calculate FFT
        fft_data = np.fft.fft(data, axis=0)
        freqs = np.fft.fftfreq(len(data), 1/256)  # 256 Hz sampling rate
        
        # Calculate power in each band
        powers = {}
        for band, (low, high) in self.freq_bands.items():
            # Find frequencies in band
            mask = (freqs >= low) & (freqs <= high)
            # Calculate average power across channels
            band_power = np.mean(np.abs(fft_data[mask]))
            powers[band] = float(band_power)
        
        return powers
    
    def calculate_khushu_percentage(self, powers):
        """Calculate Khushu percentage from band powers"""
        # Normalize powers
        total_power = sum(powers.values())
        if total_power == 0:
            return 0
        
        normalized_powers = {band: power/total_power 
                           for band, power in powers.items()}
        
        # Calculate weighted sum
        score = sum(self.band_weights[band] * normalized_powers[band] 
                   for band in self.freq_bands.keys())
        
        # Convert to percentage (0-100)
        khushu_percentage = max(0, min(100, (score + 0.5) * 100))
        
        return khushu_percentage
    
    def calibrate(self):
        """Calibrate baseline alpha levels"""
        print("\nCalibrating (5 seconds)...")
        calibration_data = []
        start_time = time.time()
        
        while time.time() - start_time < 5:
            sample, _ = self.eeg_inlet.pull_sample()
            if sample:
                calibration_data.append(sample[:4])  # First 4 channels
        
        if calibration_data:
            powers = self.calculate_band_powers(calibration_data)
            self.alpha_baseline = powers['alpha']
            self.alpha_std = stdev([x[0] for x in calibration_data])
            print("✅ Calibration complete!")
        else:
            print("❌ Calibration failed - no data received")
    
    def save_results_to_csv(self):
        """Save average Khushu level to CSV"""
        if not self.khushu_values:
            return
        
        avg_khushu = mean(self.khushu_values)
        with open(self.csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f'Test {self.test_number}', f'{avg_khushu:.2f}'])
    
    def save_detailed_data_to_csv(self, current_time, powers, khushu_percentage):
        """Save detailed time-series data to CSV"""
        # Always start with 'w' mode for the first data point to clear previous session
        if current_time == self.times[0]:  # First data point of the session
            mode = 'w'  # overwrite mode
        else:
            mode = 'a'  # append mode
        
        with open(self.detailed_csv_filename, mode, newline='') as f:
            writer = csv.writer(f)
            if mode == 'w':  # Only write headers when creating new file
                writer.writerow([
                    'time', 
                    'DP',  # Delta Power
                    'TP',  # Theta Power
                    'AP',  # Alpha Power
                    'BP',  # Beta Power
                    'GP',  # Gamma Power
                    'KI'   # Khushu Index
                ])
            
            # Write the data row
            writer.writerow([
                f'{current_time:.2f}',
                f'{powers["delta"]:.2f}',
                f'{powers["theta"]:.2f}',
                f'{powers["alpha"]:.2f}',
                f'{powers["beta"]:.2f}',
                f'{powers["gamma"]:.2f}',
                f'{khushu_percentage:.2f}'
            ])
    
    def start_monitoring(self):
        self.calibrate()
        
        print("\nStarting Khushu monitoring...\n")
        window_size = 256
        eeg_buffer = []
        start_time = time.time()
        last_data_time = time.time()
        
        try:
            while True:
                sample, timestamp = self.eeg_inlet.pull_sample(timeout=0.1)
                current_time = time.time()
                
                if current_time - last_data_time > 2.0:
                    print("\n⚠️ No data received for 2 seconds. Check Muse connection!")
                
                if sample:
                    last_data_time = current_time
                    eeg_buffer.append(sample[:4])  # Only take first 4 channels
                
                if len(eeg_buffer) >= window_size:
                    # Calculate powers in all frequency bands
                    powers = self.calculate_band_powers(eeg_buffer)
                    khushu_percentage = self.calculate_khushu_percentage(powers)
                    
                    # Update data for plotting
                    elapsed_time = current_time - start_time
                    self.times.append(elapsed_time)
                    
                    for band, power in powers.items():
                        self.band_values[band].append(power)
                    
                    self.khushu_values.append(khushu_percentage)
                    
                    # Save detailed data
                    self.save_detailed_data_to_csv(elapsed_time, powers, khushu_percentage)
                    
                    # Update feedback text
                    feedback = f"Khushu Level: {khushu_percentage:.1f}%\n"
                    feedback += f"Alpha/Theta Ratio: {powers['alpha']/powers['theta']:.2f}\n"
                    
                    if khushu_percentage >= 90:
                        feedback += "Exceptional spiritual focus!"
                    elif khushu_percentage >= 75:
                        feedback += "Excellent focus"
                    elif khushu_percentage >= 60:
                        feedback += "Good focus!"
                    elif khushu_percentage >= 40:
                        feedback += "Moderate focus"
                    else:
                        feedback += "Mind may be wandering..."
                    
                    self.feedback_text.set_text(feedback)
                    self.update_plots()
                    
                    eeg_buffer = []
                
                plt.pause(0.01)
                
        except KeyboardInterrupt:
            print("\nStopping Khushu monitoring...")
            self.save_results_to_csv()
            self.test_number += 1
            plt.close('all')
        except Exception as e:
            print(f"\n❌ Error during monitoring: {e}")
            print("Please check your Muse connection and try again")
            plt.close('all')

if __name__ == "__main__":
    monitor = KhushuMonitor()
    monitor.start_monitoring() 