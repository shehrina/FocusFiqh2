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
        
        # Initialize empty data for each band
        self.band_values = {band: [] for band in self.freq_bands}
        
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
        
        # Data for plotting
        self.times = []
        self.khushu_values = []
        
        # Initialize khushu line
        self.khushu_line, = self.ax2.plot([], [], 'g-', linewidth=2, label='Khushu Level')
        self.ax2.legend(loc='upper right')
        
        # Text display for feedback
        self.feedback_text = self.fig.text(0.02, 0.02, '', color='white', fontsize=12,
                                         bbox=dict(facecolor='black', alpha=0.7))
        
        plt.tight_layout()
        self.fig.canvas.draw()
    
    def update_plots(self):
        """Update the plots with new data"""
        if len(self.times) > 1:
            # Keep only last 10 seconds of data
            window = 10
            if self.times[-1] - self.times[0] > window:
                start_idx = next(i for i, t in enumerate(self.times) 
                               if t > self.times[-1] - window)
                self.times = self.times[start_idx:]
                for band in self.band_values:
                    self.band_values[band] = self.band_values[band][start_idx:]
                self.khushu_values = self.khushu_values[start_idx:]
            
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
        """Calculate power in different frequency bands"""
        data = np.array(eeg_data)
        fft_data = np.fft.fft(data, axis=0)
        freqs = np.fft.fftfreq(len(data), 1/256)  # 256 Hz sampling rate
        
        powers = {}
        for band, (low, high) in self.freq_bands.items():
            # Extract band power
            mask = (freqs >= low) & (freqs <= high)
            powers[band] = np.mean(np.abs(fft_data[mask]))
            
        return powers
    
    def calibrate(self):
        """Calibrate by measuring baseline alpha activity"""
        print("\nCalibration Phase")
        print("Please relax and look straight ahead for 10 seconds...")
        
        alpha_powers = []
        eeg_buffer = []
        start_time = time.time()
        
        while time.time() - start_time < 10:
            sample, _ = self.eeg_inlet.pull_sample()
            if sample:
                eeg_buffer.append(sample[:4])
                
                if len(eeg_buffer) >= 256:  # Process in 1-second chunks
                    alpha_power = self.calculate_band_powers(eeg_buffer)['alpha']
                    alpha_powers.append(alpha_power)
                    eeg_buffer = []
                    print(".", end="", flush=True)
        
        print("\nCalibration complete!")
        
        # Set baseline as average alpha power during calibration
        self.alpha_baseline = mean(alpha_powers) if alpha_powers else 1000
        self.alpha_std = stdev(alpha_powers) if len(alpha_powers) > 1 else 100
        
        print(f"Baseline Alpha Power: {self.alpha_baseline:.2f}")
    
    def calculate_khushu_percentage(self, powers):
        """
        Calculate khushu percentage based on band powers
        Using insights from the paper about alpha wave dominance in meditation
        """
        # Normalize powers
        total_power = sum(powers.values())
        if total_power == 0:
            return 0
            
        normalized_powers = {
            band: power/total_power 
            for band, power in powers.items()
        }
        
        # Calculate weighted score
        score = sum(
            self.band_weights[band] * normalized_powers[band]
            for band in self.freq_bands.keys()
        )
        
        # Convert to percentage (0-100)
        # Score will be higher when alpha is dominant (meditation state)
        khushu_percentage = max(0, min(100, (score + 0.5) * 100))
        
        return khushu_percentage
    
    def save_results_to_csv(self):
        """Save average khushu index to CSV file"""
        avg_khushu = mean(self.khushu_values) if self.khushu_values else 0
        
        # Create CSV with headers if it doesn't exist
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Test Number', 'Average Khushu Index'])
        
        # Append results
        with open(self.csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f'Test {self.test_number}', f'{avg_khushu:.2f}'])
    
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
                
                # Check if we haven't received data for too long
                if current_time - last_data_time > 2.0:
                    print("\n⚠️ No data received for 2 seconds. Check Muse connection!")
                
                if sample:
                    last_data_time = current_time
                    eeg_buffer.append(sample[:4])
                
                if len(eeg_buffer) >= window_size:
                    # Calculate powers in all frequency bands
                    powers = self.calculate_band_powers(eeg_buffer)
                    khushu_percentage = self.calculate_khushu_percentage(powers)
                    
                    # Update data for plotting
                    self.times.append(current_time - start_time)
                    
                    for band, power in powers.items():
                        if band not in self.band_values:
                            self.band_values[band] = []
                        self.band_values[band].append(power)
                    
                    self.khushu_values.append(khushu_percentage)
                    
                    # Update feedback text with more detailed information
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