from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/data', methods=['GET', 'POST', 'OPTIONS'])
def data():
    print("Request received!")
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    print("Server starting on port 3000...")
    print("Press Ctrl+C to quit")
    app.run(host='0.0.0.0', port=3000)