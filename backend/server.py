from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import csv
import subprocess
import signal
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Global variable to store the process
khushu_process = None

@app.route("/", methods=["GET"])
def get_csv_data():
    try:
        with open('detailed_session.csv', 'r') as f:
            # Skip the header row
            next(f)
            return Response(f.read(), mimetype='text/csv')
    except FileNotFoundError:
        return "No data available yet", 204
    except Exception as e:
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

@app.route("/start_demo", methods=["POST", "OPTIONS"])
def start_demo():
    global khushu_process
    
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
        
    try:
        # If process is already running, don't start a new one
        if khushu_process and khushu_process.poll() is None:
            return jsonify({"status": "success", "message": "Demo already running"})
            
        # Clear existing CSV file
        with open('detailed_session.csv', 'w') as f:
            f.write('time,DP,TP,AP,BP,GP,KI\n')
            
        # Start khushu_index.py
        khushu_process = subprocess.Popen(['python', 'khushu_index.py'])
        return jsonify({"status": "success", "message": "Demo started"})
    except Exception as e:
        if khushu_process:
            khushu_process.terminate()
            khushu_process = None
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/end_demo", methods=["POST", "OPTIONS"])
def end_demo():
    global khushu_process
    
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        response = jsonify({"status": "success"})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
        
    try:
        if khushu_process:
            khushu_process.send_signal(signal.SIGINT)
            khushu_process.wait()
            khushu_process = None
        return jsonify({"status": "success", "message": "Demo ended"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)