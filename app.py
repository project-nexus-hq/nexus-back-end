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

USER-PROVIDED CONSTRAINTS (THE SOURCE OF TRUTH):
1. CLEARANCE: The user will provide their current clearance level. Do NOT suggest career goals or training that require a higher clearance unless you explicitly label it as "Requires Upgrade to [Level]."
2. EXISTING CERTS: The user will list certifications they already possess. Do NOT include these as a step in the learning path.
3. LOCAL SOPs: If unit-level context or an SOP is provided, prioritize the technical tasks and tools mentioned in that context over generic industry equivalents.

When you receive the user's mission profile, consider the following:
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
    
    # Extract the new structured JSON payload from the frontend
    mission_profile = data.get('missionProfile')
    if not mission_profile:
        # Fallback to legacy single prompt for backward compatibility during testing
        user_prompt = data.get('prompt')
        if not user_prompt:
            return jsonify({"error": "No mission profile or prompt provided"}), 400
    else:
        # Construct a highly structured prompt from the JSON constraints
        certs_held = ", ".join(mission_profile.get("currentCertifications", [])) or "None"
        local_context = mission_profile.get("localContextSop", "None provided.")
        
        user_prompt = f"""
        MISSION PROFILE OVERVIEW:
        - Target Role / Goal: {mission_profile.get("strategicGoal", "Unspecified")} ({mission_profile.get("targetRoleType", "Unspecified")})
        - Clearance Level: {mission_profile.get("clearanceLevel", "Unclassified")}
        - Certifications Already Held: {certs_held}
        - Unit Context / SOPs: {local_context}
        
        Please generate a learning path tailored strictly to these constraints.
        """

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
        
        # Extract the learning_path key
        plan = parsed.get("learning_path", [])
        
        # Handle the Out of Scope edge case cleanly
        if not plan:
            return jsonify([{"step_number": 1, "title": "Out of Scope", "justification": "Query unrelated to cyber operations.", "platform_url": "", "access_instructions": ""}])
        
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
