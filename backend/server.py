from flask import Flask, Response, jsonify
from flask_cors import CORS
import csv
import subprocess
import signal
import os

app = Flask(__name__)
CORS(app)

# Global variable to store the process
khushu_process = None

@app.route("/", methods=["GET"])
def get_csv_data():
    try:
        with open('detailed_session.csv', 'r') as f:
            # Skip the header row
            next(f)
            # Return all data rows without headers
            return Response(f.read(), mimetype='text/plain')
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

@app.route("/start_demo", methods=["POST"])
def start_demo():
    global khushu_process
    try:
        # Start khushu_index.py as a subprocess
        khushu_process = subprocess.Popen(['python', 'khushu_index.py'])
        return jsonify({"status": "success", "message": "Demo started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/end_demo", methods=["POST"])
def end_demo():
    global khushu_process
    try:
        if khushu_process:
            # Send SIGINT (Ctrl+C) to the process
            khushu_process.send_signal(signal.SIGINT)
            khushu_process.wait()  # Wait for the process to finish
            khushu_process = None
        return jsonify({"status": "success", "message": "Demo ended"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)