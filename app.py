from flask import Flask, jsonify
from flask_cors import CORS
import os

# Create the Flask application object
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# This is the test API endpoint
@app.route('/run/predict', methods=['POST'])
def predict():
    data = request.get_json()
    user_prompt = data.get('prompt')
    print(f"API endpoint was hit with promt: {user_prompt}")
    
    dummy_plan = [
        {"step_number": 1, "title": "CompTIA Network+ Certification (from Flask)", "justification": "This response proves the Flask backend is working.", "url": "https://www.comptia.org/certifications/network"},
        {"step_number": 2, "title": "Introduction to Python for Automation", "justification": "This confirms the connection is successful.", "url": "https://www.udemy.com/course/python-for-network-engineers/"}
    ]
    
    return jsonify(dummy_plan)

# This is a simple "health check" endpoint
@app.route('/')
def status():
    return "Flask server is alive and running with explicit, permissive CORS enabled!"

# This block is only used for local testing
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
