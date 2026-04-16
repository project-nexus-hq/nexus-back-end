from flask import Flask, jsonify, request, make_response
import anthropic
import json
import os

from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://project-nexus-hq.github.io"])

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system="""You are a DAF (Department of the Air Force) cyber career advisor. 
Your job is to generate personalized, realistic training plans for cyber operators.

When given a user's current role and career goal, respond ONLY with a valid JSON array.
Each object in the array must have exactly these keys:
- "step_number": integer starting at 1
- "title": string, the name of the certification, course, or training resource
- "justification": string, 1-2 sentences explaining why this step matters for their specific goal
- "url": string, a real and accurate URL to the resource

Prioritize resources in this order:
1. Official DAF/DoD resources (AETC, JKO, Cyber Excepted Service, Air University)
2. Industry certifications relevant to DoD work (CompTIA, SANS/GIAC, ISC2, Offensive Security)
3. Reputable free platforms (TryHackMe, HackTheBox, Cybrary, NICCS)

Generate between 5 and 7 steps. Output only the JSON array with no markdown, no explanation, no preamble.""",
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    raw_text = message.content[0].text

    # Strip markdown code fences if Claude includes them despite instructions
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    plan = json.loads(cleaned)
    return jsonify(plan)

@app.route('/')
def status():
    return "Flask server is alive and running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
