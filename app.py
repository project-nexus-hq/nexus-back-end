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

# =======================================================
# PROMPT 1: STUDENT PORTAL - CAREER ADVISOR
# =======================================================
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
- ADVANCED TRANSITIONS: Use 5 to 7 steps for complex transitions (like 1D7 to 1B4). Every single step MUST have a direct, actionable technical requirement (e.g., OS internals, Python/C scripting, advanced DCO/OCO concepts, and so on).
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

# =======================================================
# PROMPT 2: INSTRUCTOR PORTAL - CLOSED BOOK REVIEWER
# =======================================================
MTP_TUTOR_PROMPT = """You are a strict Master Training Plan (MTP) Tutor and Curriculum Reviewer. You operate as a "Closed-Book" AI.

CRITICAL RULES:
1. STRICT GROUNDING: You must base your answers STRICTLY and EXCLUSIVELY on the provided Document/MTP text. 
2. NO OUTSIDE KNOWLEDGE: Do NOT use pre-trained knowledge, internet sources, or external training platforms UNLESS they are explicitly written in the provided document.
3. INTERNAL REVIEW & ADJUSTMENTS: If the user asks how to "adjust," "change," or "critique" the document, you must answer by first stating what the document CURRENTLY says, and then offering suggestions based purely on internal logic and structure. Do not invent external standards.
4. REFUSAL PROTOCOL: You must refuse to answer questions about entirely unrelated topics (like cooking or pop culture). However, if the user asks a hypothetical question about the MTP's rules (e.g., "What if a student wants to skip a phase?"), you MUST answer by quoting the current rule from the text.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object containing one key:
1. "assistant_message": A string containing your answer based purely on the document text. Format with clear, readable spacing using HTML line breaks (<br><br>) for paragraphs.

Output only the JSON object. No preamble, no markdown."""

# =======================================================
# PROMPT 3: TUTOR PORTAL - SOCRATIC LEARNING
# =======================================================
SOCRATIC_TUTOR_PROMPT = """You are a Socratic Military Cyber Instructor. Your mission is to help a student understand and complete the tasks listed in their uploaded unit training document.

CRITICAL RULES:
1. THE HYBRID APPROACH: You MUST use the uploaded document as your syllabus. However, you ARE permitted to use external technical knowledge to actually teach the tools and concepts mentioned in that document.
2. NO DIRECT ANSWERS: If a student asks "How do I do X?", do NOT just give them the exact command or code. Instead, ask them a guiding question or explain the underlying concept so they figure it out themselves.
3. STAY ON TARGET: If the student asks about a tool, framework, or concept that is NOT listed in the document, you must politely redirect them back to the tasks required by the document.
4. TONE: Encouraging but firm, like a seasoned NCO mentoring an airman.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object containing one key:
1. "assistant_message": A string containing your Socratic response. Format with clear, readable spacing using HTML line breaks (<br><br>) for paragraphs.

Output only the JSON object. No preamble, no markdown."""


# =======================================================
# ROUTE 1: STUDENT PORTAL (PREDICT)
# =======================================================
@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
   if request.method == 'OPTIONS':
      response = make_response()
      response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
      response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
      response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
      return response, 200

   data = request.get_json()
   chat_history = data.get('chatHistory', [])
   mission_profile = data.get('missionProfile', {})
    
   profile_context = f"""
   --- USER MISSION PROFILE ---
   Current Clearance: {mission_profile.get('clearanceLevel', 'Unclassified')}
   Certifications Held: {", ".join(mission_profile.get('currentCertifications', [])) or 'None'}
   Unit Context: {mission_profile.get('localContextSop', 'None provided.')}
   """

   messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{profile_context}"}]
    
   for msg in chat_history:
      messages.append({"role": msg["role"], "content": msg["content"]})

   try:
      completion = client.chat.completions.create(
         model="llama-3.1-8b-instant",
         messages=messages,
         temperature=0.6,
         max_tokens=2048,
         response_format={"type": "json_object"} 
      )
       
      raw_text = completion.choices[0].message.content.strip()
       
      if raw_text.startswith("```"):
         raw_text = raw_text.split("\n", 1)[-1]
      if raw_text.endswith("```"):
         raw_text = raw_text.rsplit("\n", 1)[0]
      if raw_text.startswith("json"):
         raw_text = raw_text[4:].strip()

      parsed_response = json.loads(raw_text.strip())
        
      if "learning_path" not in parsed_response:
         parsed_response["learning_path"] = []
      if "assistant_message" not in parsed_response:
         parsed_response["assistant_message"] = "I have updated your roadmap based on our conversation."

      return jsonify(parsed_response)
       
   except Exception as e:
      # Return the exact exception message in the response
      print(f"ERROR DETAILS: {str(e)}")
      return jsonify({"error": str(e), "type": type(e).__name__}), 500

# =======================================================
# ROUTE 2: INSTRUCTOR PORTAL (CLOSED BOOK MTP)
# =======================================================
@app.route('/run/mtp_chat', methods=['POST', 'OPTIONS'])
def mtp_chat():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    chat_history = data.get('chatHistory', [])
    mtp_content = data.get('mtpData', '')

    if not mtp_content:
        return jsonify({"assistant_message": "Error: No document data found. Please ingest a document first."})

    messages = [{"role": "system", "content": f"{MTP_TUTOR_PROMPT}\n\n--- UPLOADED DOCUMENT ---\n{mtp_content}"}]
    
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
       
        raw_text = completion.choices[0].message.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("\n", 1)[0]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

        parsed_response = json.loads(raw_text.strip())
       
        return jsonify(parsed_response)
       
    except Exception as e:
       # Return the exact exception message in the response
       print(f"ERROR DETAILS: {str(e)}")
       return jsonify({"error": str(e), "type": type(e).__name__}), 500


# =======================================================
# ROUTE 3: TUTOR PORTAL (SOCRATIC LEARNING)
# =======================================================
@app.route('/run/tutor_chat', methods=['POST', 'OPTIONS'])
def tutor_chat():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    chat_history = data.get('chatHistory', [])
    mtp_content = data.get('mtpData', '')

    if not mtp_content:
        return jsonify({"assistant_message": "Error: No training document found. Please load your syllabus first."})

    messages = [{"role": "system", "content": f"{SOCRATIC_TUTOR_PROMPT}\n\n--- UPLOADED SYLLABUS ---\n{mtp_content}"}]
    
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4, # Mid-level temp for Socratic creativity
            max_tokens=2048,
            response_format={"type": "json_object"} 
        )
       
        raw_text = completion.choices[0].message.content.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("\n", 1)[0]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

        parsed_response = json.loads(raw_text.strip())
       
        return jsonify(parsed_response)
       
    except Exception as e:
       # Return the exact exception message in the response
       print(f"ERROR DETAILS: {str(e)}")
       return jsonify({"error": str(e), "type": type(e).__name__}), 500

# =======================================================
# STATUS
# =======================================================
@app.route('/')
def status():
    return "Project Nexus Command Server is Active."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
