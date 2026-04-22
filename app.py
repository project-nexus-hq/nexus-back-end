from flask import Flask, jsonify, request, make_response
from groq import Groq
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://project-nexus-hq.github.io"])

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a cyber career advisor with experience in both the Department of the Air Force (DAF) and the private sector.
Your job is to generate personalized, realistic training plans for cyber operators. Your priority is to recommend training and learning resources, not just certifications and degrees.
When you receive the user's current role and desired objective, consider the following at minimum:
- What skills or certs should the user obtain that would not already be provided in their stated current role?
- Since the private sector is traditionally the "front line" in cyber conflict, what skills and certs does the private sector value when pursuing the user's desired goal or role?
- What DOD-funded resources are available that can provide this training to service members at no cost to them or their unit?
- If no DOD-funded resources are available, what other credible and free resources can you recommend to the user?

When given a user's current role and career goal, respond ONLY with a valid JSON array.
Each object in the array must have exactly these keys:
- "step_number": integer starting at 1
- "title": string, the name of the certification, course, or training resource
- "justification": string, 1-2 sentences explaining why this step matters for their specific goal
- "url": string, a real and accurate URL to the resource

Prioritize resources in this order:
1. Known DAF/DoD-funded technical resources (O'Reilly Media access through MWR Libraries, DigitalU, Percipio)
2. Reputable free platforms (TryHackMe, HackTheBox, Cybrary, Cisco NetACad)
3. If a certification or type of certification is the goal, choose those relevant to DoD work (CompTIA, SANS/GIAC, ISC2, Offensive Security)

You are not limited to these resources. This is simply a starting point for you.
Generate between 5-7 steps, but adjust as needed if the goal is very short-term or requires a long-term education.
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
