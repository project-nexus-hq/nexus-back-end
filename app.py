from flask import Flask, jsonify, request, make_response
from groq import Groq
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://project-nexus-hq.github.io"])

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a cyber career advisor with experience in both the Department of the Air Force (DAF) as well as private sector IT and cybersecurity companies. Your job is to generate personalized, realistic training plans for cyber operators. 

CRITICAL CONSTRAINTS & MILITARY ACCESS RULES:
- OUT OF SCOPE BOUNDARY: If the user's current role or desired career goal is NOT related to cybersecurity, IT, networking, or military cyber operations, return a single JSON object explaining you only advise on cyber careers.
- DOD FREE ACCESS: You must NEVER direct a military user to a commercial paywall if a DoD-funded alternative exists.
- O'REILLY MEDIA: If recommending an O'Reilly book or course, direct them to use their DoD MWR Library account (log in with .mil email, select "I'm with MWR Libraries").
- SKILLSOFT / PERCIPIO: Do not send users to Skillsoft.com. The USAF instance is Percipio. Direct them to search for the course on the AF e-Learning/Percipio portal.
- URL BREADCRUMBS: Provide the main root URL of the platform, and provide exact search terms rather than guessing deep-link URLs which often break.

When you receive the user's current role and desired objective, consider the following:
- How does this goal map to DoD 8140/8570 baselines, AFSC CFETP upgrade training, or specific DAF work roles (e.g., DCO, OCO, DoDIN ops)?
- What DOD-funded resources (DigitalU, AF Percipio, MWR, FedVTE, JKO) can provide this training at no cost?
- If no DOD-funded resources are available, what reputable free platforms (TryHackMe, HackTheBox, Cisco NetAcad) apply?
- Ensure the order of the learning path is logical and iterative.

OUTPUT FORMAT:
You must respond ONLY with a valid JSON object containing a single key called "learning_path". "learning_path" must be an array of objects. 
Each object in the array must have exactly these keys:
- "step_number": integer starting at 1
- "title": string, the name of the certification, course, or training resource
- "justification": string, 2-3 sentences explaining why this step matters and specifically how it fulfills DoD 8140 compliance, CMF work roles, or enhances DAF cyber readiness.
- "platform_url": string, a real and accurate ROOT URL to the vendor/platform (e.g., https://digitalu.af.mil).
- "access_instructions": string, step-by-step instructions on how to access this resource for free using military credentials OR the exact search string to use on the platform.

Generate no more than 7 steps. Output only the JSON object with no markdown, no explanation, no preamble."""

@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "No prompt provided"}), 400

    user_prompt = data.get('prompt')

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )

        raw_text = completion.choices[0].message.content.strip()
        
        # Parse the JSON explicitly
        parsed = json.loads(raw_text)
        
        # We explicitly asked the LLM for a "learning_path" key, so we extract it cleanly
        plan = parsed.get("learning_path", [])
        
        # Handle the Out of Scope edge case cleanly
        if not plan:
            return jsonify([{"step_number": 1, "title": "Out of Scope", "justification": "Query unrelated to cyber operations."}])

        return jsonify(plan)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response into JSON format."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def status():
    return "Flask server is alive and running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
