from flask import Flask, jsonify, request, make_response
from groq import Groq
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://project-nexus-hq.github.io"])

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a cyber career advisor with experience in both the Department of the Air Force (DAF) as well as private sector IT 
and cybersecurity companies. Your job is to generate personalized, realistic training plans for cyber operators. Your priority is to recommend 
an iterative path made of training and learning resources, not just certifications and degrees.

When you receive the user's current role and desired objective, consider the following at minimum:
- What training should the user pursue that would not already be provided through working in their current role?
- Prioritize training and certs valued by industry and the civilian IT and cybersecurity community over those valued by the DOD.
- What DOD-funded resources are available that can provide this training to service members at no cost to them or their unit?
- If no DOD-funded resources are available, what other credible and free resources can you recommend to the user?
- Is the order of the learning path iterative? Are there any redundant or unecessary steps?

When given a user's current role and career goal, respond ONLY with a valid JSON array.
Each object in the array must have exactly these keys:
- "step_number": integer starting at 1
- "title": string, the name of the certification, course, or training resource
- "justification": string, 1-2 sentences explaining why this step matters for their specific goal
- "url": string, a real and accurate URL to the resource

Prioritize resources in this order:
1. Known DAF/DoD-funded technical resources (O'Reilly Media access through MWR Libraries, DigitalU, Percipio)
2. Reputable free platforms (TryHackMe, HackTheBox, Cybrary, Cisco NetACad, vendor-provided courses and labs to teach about their own products)
3. If a particular certification is the goal, understand the publicly available components of the cert's exam and recommend courses that teach them. The goal here is to provide a free alternative to a paid bootcamp.

You are not limited to these resources. This is simply a starting point for you.
Generate no more than 7 steps. Do not add extra steps just to satisfy this requirement - only include what is relevant to the user's goal.
Output only the JSON array with no markdown, no explanation, no preamble."""

@app.route('/run/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = 'https://project-nexus-hq.github.io'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    data = request.get_json()
    user_prompt = data.get('prompt')

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2048,
        response_format={"type": "json_object"}  # Groq's JSON mode — cleaner than string parsing
    )

    raw_text = completion.choices[0].message.content.strip()
    parsed = json.loads(raw_text)

    # Groq's json_object mode wraps arrays in an object — unwrap if needed
    if isinstance(parsed, dict):
        plan = next(iter(parsed.values()))
    else:
        plan = parsed

    return jsonify(plan)

@app.route('/')
def status():
    return "Flask server is alive and running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
