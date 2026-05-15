from flask import Flask, jsonify, request, make_response
from groq import Groq
import json
import os
from flask_cors import CORS

app = Flask(__name__)

# Allow your GitHub Pages frontend to communicate with this backend
CORS(app, origins=["https://project-nexus-hq.github.io"])

# Initialize Groq client using your environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- THE SYSTEM BRAIN ---
# This prompt ensures the AI follows DoD rules and returns structured data
SYSTEM_PROMPT = """You are a cyber career advisor with experience in the Department of the Air Force (DAF) and private sector IT. 

MISSION: Generate personalized training plans for cyber operators using the "Mission Profile" constraints provided.

CRITICAL ACCESS RULES:
- DOD FREE ACCESS: NEVER direct a military user to a commercial paywall if a DoD-funded alternative exists.
- O'REILLY MEDIA: Direct them to use their DoD MWR Library account.
- SKILLSOFT / PERCIPIO: Direct them to search on the AF e-Learning/Percipio portal.
- URL BREADCRUMBS: Provide the main root URL of the platform and exact search terms.

USER-PROVIDED CONSTRAINTS (THE SOURCE OF TRUTH):
1. CLEARANCE: Respect the user's stated clearance level. Do NOT suggest training requiring a higher level unless explicitly labeled as an upgrade path.
2. EXISTING CERTS: Do NOT include certifications the user already possesses in the roadmap.
3. LOCAL SOPs: Prioritize the technical tasks/tools mentioned in provided unit documents.

OUTPUT FORMAT:
You must respond ONLY with a valid JSON object containing exactly two keys:
1. "assistant_message": A string containing your conversational response to the user's input.
2. "learning_path": An array of objects. Each object must have:
   - "step_number": integer
   - "title": string
   - "justification": string (2-3 sentences on mission impact/8140 compliance)
   - "platform_url": string (ROOT URL)
   - "access_instructions": string (step-by-step for military users)

Output only the JSON object. No preamble, no markdown."""

@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Handle the "Pre-flight" check for security (CORS)
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    
    # NEW: Expecting chat history and the mission profile (clearance, etc.)
    chat_history = data.get('chatHistory', [])
    mission_profile = data.get('missionProfile', {})
    
    # 1. Build the AI's "Context" from the Mission Profile
    profile_context = f"""
    --- USER MISSION PROFILE ---
    Current Clearance: {mission_profile.get('clearanceLevel', 'Unclassified')}
    Certifications Held: {", ".join(mission_profile.get('currentCertifications', [])) or 'None'}
    Unit Context: {mission_profile.get('localContextSop', 'None provided.')}
    Strategic Goal: {mission_profile.get('strategicGoal', 'General Career Advice')}
    """

    # 2. Prepare the messages for the LLM
    # We start with the System Instructions + the User's Profile Facts
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{profile_context}"}]
    
    # 3. Add the actual conversation history
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        # Request a JSON response from Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
        
        raw_text = completion.choices[0].message.content.strip()
        parsed_response = json.loads(raw_text)
        
        # Ensure the response has the required keys before sending to frontend
        if "learning_path" not in parsed_response:
            parsed_response["learning_path"] = []
        if "assistant_message" not in parsed_response:
            parsed_response["assistant_message"] = "I have updated your roadmap based on our conversation."

        return jsonify(parsed_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def status():
    return "Project Nexus Command Server is Active."

if __name__ == "__main__":
    # Use the port assigned by the environment (e.g., Render or Heroku)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
