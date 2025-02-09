from flask import Flask, Response, jsonify
from flask_cors import CORS
import csv
import subprocess
import signal
import os
import sys
import time
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

# Global variables
khushu_process = None
USE_SIMULATED_DATA = True  # Flag to use simulated data instead of live Muse data
current_index = 0

def generate_simulated_data():
    global current_index
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'detailed_session.csv')
    
    try:
        df = pd.read_csv(csv_path)
        if current_index >= len(df):
            current_index = 0
        
        # Get current row
        row = df.iloc[current_index]
        current_index += 1
        
        # Write to CSV
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                row['time'],
                row['DP'],
                row['TP'],
                row['AP'],
                row['BP'],
                row['GP'],
                row['KI']
            ])
            
    except Exception as e:
        print(f"Error generating simulated data: {e}")

@app.route("/", methods=["GET"])
def get_csv_data():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, 'detailed_session.csv')
        
        with open(csv_path, 'r') as f:
            # Skip the header row
            next(f)
            # Return all data rows without headers
            return Response(f.read(), mimetype='text/plain')
    except FileNotFoundError:
        return "No data available yet", 204
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return str(e), 500

@app.route("/data", methods=["GET"])
def get_latest_data():
    try:
        with open('detailed_session.csv', 'r') as f:
            # Skip the header row
            next(f)
            # Get the last line of data
            for line in f:
                last_line = line
            
            # Parse the last line
            time, dp, tp, alpha, bp, gp, khushu = last_line.strip().split(',')
            
            return jsonify({
                "status": "processing",
                "time": float(time),
                "band_powers": {
                    "alpha": float(alpha)
                },
                "khushu_percentage": float(khushu),
                "alpha_theta_ratio": 1.0
            })
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "No data available yet"}), 204
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/start_demo", methods=["POST"])
def start_demo():
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Clear the existing CSV file if it exists
        csv_path = os.path.join(current_dir, 'detailed_session.csv')
        with open(csv_path, 'w') as f:
            f.write('time,DP,TP,AP,BP,GP,KI\n')
        
        # Start khushu_index.py as a subprocess
        khushu_script_path = os.path.join(current_dir, 'khushu_index.py')
        if not os.path.exists(khushu_script_path):
            raise FileNotFoundError(f"khushu_index.py not found at {khushu_script_path}")
        
        python_executable = sys.executable
        khushu_process = subprocess.Popen(
            [python_executable, khushu_script_path], 
            cwd=current_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return jsonify({"status": "success", "message": "Demo started successfully"})
    except Exception as e:
        print(f"Error starting demo: {str(e)}")
        if khushu_process:
            khushu_process.terminate()
            khushu_process = None
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route("/end_demo", methods=["POST"])
def end_demo():
    global khushu_process
    try:
        if khushu_process:
            khushu_process.terminate()
            khushu_process = None
        return jsonify({"status": "success", "message": "Demo ended"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)