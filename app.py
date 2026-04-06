from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://project-nexus-hq.github.io"])

@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Explicitly handle the preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    user_prompt = data.get('prompt')
    print(f"API endpoint was hit with prompt: {user_prompt}")
    
    dummy_plan = [
        {"step_number": 1, "title": "CompTIA Network+ Certification (from Flask)", "justification": "This response proves the Flask backend is working.", "url": "https://www.comptia.org/certifications/network"},
        {"step_number": 2, "title": "Introduction to Python for Automation", "justification": "This confirms the connection is successful.", "url": "https://www.udemy.com/course/python-for-network-engineers/"}
    ]
    
    return jsonify(dummy_plan)

@app.route('/')
def status():
    return "Flask server is alive and running with OPTIONS enabled!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
