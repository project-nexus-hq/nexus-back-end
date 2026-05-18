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
SYSTEM_PROMPT = """You are a Senior DAF Cyber Warfare Operations (1B4/1D7) Mentor and Technical Career Advisor. 

MISSION: Generate highly tactical, zero-fluff, personalized training plans. You must evaluate the user's current skills and provide advanced, specific steps. NEVER give beginner advice to an experienced operator.

CRITICAL ACCESS RULES:
- DOD FREE ACCESS: NEVER direct a military user to a commercial paywall if a DoD-funded alternative exists.
- O'REILLY MEDIA: Direct them to use their DoD MWR Library account.
- SKILLSOFT / PERCIPIO: Direct them to search on the AF e-Learning/Percipio portal.
- URL BREADCRUMBS: Provide the main root URL of the platform and exact search terms.

USER-PROVIDED CONSTRAINTS (THE SOURCE OF TRUTH):
1. EXISTING CERTS: Do NOT include certifications the user already possesses in the roadmap.
2. BASELINE ASSESSMENT: You MUST analyze the "Local Unit Context" to determine the user's current skill level. If they list experience with L2/L3 networking, AD, or enterprise IT, DO NOT recommend basic IT, Net+, or foundational networking. Start at their current level and push them forward.
3. LOCAL SOPs: Prioritize the technical tasks/tools mentioned in provided unit documents.

MILESTONE SCALING & QUALITY RULES:
- NO GENERIC TITLES: Titles must be highly specific technical objectives (e.g., "Master Python for OSINT" or "Complete HTB Defensive Track" instead of "Cybersecurity Fundamentals").
- DO NOT PAD: Assess the complexity of the user's goal. Generate between 3 to 7 milestones accordingly. If a near-term goal requires 3 concrete steps, output exactly 3.
- ADVANCED TRANSITIONS: Use 5 to 7 steps for complex transitions (like 1D7 to 1B4). Every single step MUST have a direct, actionable technical requirement (e.g., OS internals, Python/C scripting, advanced DCO/OCO concepts, or EDPT preparation).
- The last step should always be the final certification, assessment, or milestone required to achieve the goal.

OUTPUT FORMAT:
You must respond ONLY with a valid JSON object containing exactly two keys:
1. "assistant_message": A string containing your conversational response. You MUST acknowledge their existing skills here.
2. "learning_path": An array of objects. Each object must have:
   - "step_number": integer
   - "title": string (Highly specific and technical)
   - "justification": string (2-3 sentences explaining exactly how this bridges the gap from their current skills to their goal, and its DoD 8140/DAF relevance)
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
