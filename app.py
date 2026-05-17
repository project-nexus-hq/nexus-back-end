from flask import Flask, jsonify, request, make_response
from groq import Groq
import json
import os
from flask_cors import CORS

app = Flask(__name__)

# Allow your GitHub Pages frontend to communicate with this backend (PRESERVED)
CORS(app, origins=["https://project-nexus-hq.github.io"])

# Initialize Groq client using your environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- PROMPT 1: TRAINEE TACTICAL MENTOR ---
SYSTEM_PROMPT = """You are a Senior DAF Cyber Warfare Operations (1B4/1D7) Mentor and Technical Career Advisor. 

MISSION: Generate highly tactical, zero-fluff, personalized training plans. You must evaluate the user's current skills and provide advanced, specific steps. NEVER give beginner advice to an experienced operator.

CRITICAL ACCESS RULES:
- DOD FREE ACCESS: NEVER direct a military user to a commercial paywall if a DoD-funded alternative exists.
- O'REILLY MEDIA: Direct them to use their DoD MWR Library account.
- SKILLSOFT / PERCIPIO: Direct them to search on the AF e-Learning/Percipio portal.
- URL BREADCRUMBS: Provide the main root URL of the platform and exact search terms.

USER-PROVIDED CONSTRAINTS (THE SOURCE OF TRUTH):
1. EXISTING CERTS: Do NOT include certifications the user already possesses in the roadmap.
2. BASELINE ASSESSMENT: You MUST analyze the "Local Unit Context" to determine the user's current skill level. Start at their current level and push them forward.
3. LOCAL SOPs: Prioritize the technical tasks/tools mentioned in provided unit documents.
4. MASTER TRAINING PLAN (MTP): If an MTP is provided, your roadmap MUST directly align with the tasks, tools, and objectives listed in that document.

MILESTONE SCALING & QUALITY RULES:
- NO GENERIC TITLES: Titles must be highly specific technical objectives.
- DO NOT PAD: Assess the complexity of the user's goal. Generate between 3 to 7 milestones accordingly. If a near-term goal requires 3 concrete steps, output exactly 3.
- ADVANCED TRANSITIONS: Use 5 to 7 steps for complex transitions (like 1D7 to 1B4). Every single step MUST have a direct, actionable technical requirement.
- The last step should always be the final certification, assessment, or milestone required to achieve the goal.

OUTPUT FORMAT:
You must respond ONLY with a valid JSON object containing exactly two keys:
1. "assistant_message": A string containing your conversational response. You MUST acknowledge their existing skills here.
2. "learning_path": An array of objects. Each object must have:
   - "step_number": integer
   - "title": string (Highly specific and technical)
   - "justification": string (2-3 sentences explaining exactly how this bridges the gap)
   - "platform_url": string (ROOT URL)
   - "access_instructions": string (step-by-step for military users)

Output only the JSON object. No preamble, no markdown."""

# --- PROMPT 2: TRAINING CELL MTP REVIEWER ---
MTP_REVIEW_PROMPT = """You are a DAF Senior Enlisted Leader and Master Unit Training Manager (UTM). 
Your job is to review a provided Master Training Plan (MTP) or curriculum for a cyber unit.

Analyze the provided MTP text and generate a structured JSON critique. Look for:
1. Alignment with modern DoD 8140/8570 baselines.
2. Gaps in modern cyber warfare/defense tactics (e.g., missing cloud security, zero-trust, or automation/scripting).
3. Clarity and progression logic.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object containing:
1. "overall_assessment": string (1 paragraph summary of the MTP's quality)
2. "identified_gaps": array of strings (list of missing skills or outdated tools)
3. "recommendations": array of strings (actionable steps for the training cell to improve the curriculum)
"""

# =======================================================
# ROUTE 1: TRAINEE PREDICTION
# =======================================================
@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
    # Handle the "Pre-flight" check for security (CORS PRESERVED)
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    
    chat_history = data.get('chatHistory', [])
    mission_profile = data.get('missionProfile', {})
    
    # 1. Build the AI's "Context"
    profile_context = f"""
    --- USER MISSION PROFILE ---
    Current Clearance: {mission_profile.get('clearanceLevel', 'Unclassified')}
    Certifications Held: {", ".join(mission_profile.get('currentCertifications', [])) or 'None'}
    Unit Context: {mission_profile.get('localContextSop', 'None provided.')}
    Master Training Plan Data: {mission_profile.get('mtpData', 'No MTP provided.')}
    """

    # 2. Prepare the messages for the LLM
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{profile_context}"}]
    
    # 3. Add the actual conversation history
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
        
        raw_text = completion.choices[0].message.content.strip()
        parsed_response = json.loads(raw_text)
        
        if "learning_path" not in parsed_response:
            parsed_response["learning_path"] = []
        if "assistant_message" not in parsed_response:
            parsed_response["assistant_message"] = "I have updated your roadmap based on our conversation."
            
        return jsonify(parsed_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI response."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =======================================================
# ROUTE 2: TRAINING CELL MTP ANALYSIS (NEW)
# =======================================================
@app.route('/run/analyze_mtp', methods=['POST', 'OPTIONS'])
def analyze_mtp():
    # Exactly matching your CORS pre-flight block
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    mtp_content = data.get('mtpData', '')

    if not mtp_content:
        return jsonify({"error": "No MTP data provided."}), 400

    user_prompt = f"Please review this Master Training Plan and provide your critique:\n\n{mtp_content}"

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": MTP_REVIEW_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4, # Lower temperature for analytical review
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
        
        raw_text = completion.choices[0].message.content.strip()
        parsed_response = json.loads(raw_text)
        return jsonify(parsed_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def status():
    return "Project Nexus Command Server is Active."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
