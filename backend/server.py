from flask import Flask, Response
import csv

app = Flask(__name__)

@app.route("/latest-data", methods=["GET"])
def get_latest_data():
    try:
        with open('detailed_session.csv', 'r') as f:
            # Skip the header row
            next(f)
            # Return the rest of the data
            return Response(f.read(), mimetype='text/csv')
    except FileNotFoundError:
        return "No data available yet", 204
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)