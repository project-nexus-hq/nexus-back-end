from flask import Flask, jsonify
import os

# Create the Flask application object
app = Flask(__name__)

# This is the test API endpoint that your JavaScript will call.
@app.route('/run/predict', methods=['POST'])
def predict():
    print("API endpoint /run/predict was successfully hit!")
    
    # We will return the same dummy JSON data as before.
    dummy_plan = [
        {"step_number": 1, "title": "CompTIA Network+ Certification (from Flask)", "justification": "This response proves the Flask backend is working.", "url": "https://www.comptia.org/certifications/network"},
        {"step_number": 2, "title": "Introduction to Python for Automation", "justification": "This confirms the connection is successful.", "url": "https://www.udemy.com/course/python-for-network-engineers/"}
    ]
    
    # jsonify is Flask's way of creating a proper JSON response.
    return jsonify(dummy_plan)

# This is a simple "health check" endpoint.
@app.route('/')
def status():
    return "Flask server is alive and running!"

# This block is only used for local testing, not by Gunicorn.
if __name__ == "__main__":
    # We read the port from the environment, defaulting to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
