import gradio as gr
import json
import os
from flask import Flask

# --- Main Gradio App ---
# This is the same dummy logic as before.
def generate_dummy_plan(user_prompt):
    print(f"Received prompt from user: {user_prompt}") 

    dummy_plan = [
        {
            "step_number": 1,
            "title": "CompTIA Network+ Certification",
            "justification": "This is the foundational step to ensure you have a strong understanding of networking principles.",
            "url": "https://www.comptia.org/certifications/network"
        },
        {
            "step_number": 2,
            "title": "Introduction to Python for Automation",
            "justification": "Learning a scripting language is critical for automating tasks.",
            "url": "https://www.udemy.com/course/python-for-network-engineers/"
        },
        {
            "step_number": 3,
            "title": "Hands-On Red Team Tactics",
            "justification": "With networking and scripting skills, you can now begin to apply offensive security techniques.",
            "url": "https://www.oreilly.com/library/view/red-team-development/9781492044369/"
        }
    ]
    
    return json.dumps(dummy_plan, indent=2)

# Create the Gradio interface.
demo = gr.Interface(
    fn=generate_dummy_plan,
    inputs=[gr.Textbox(label="User Prompt", lines=4)],
    outputs=[gr.Textbox(label="Generated JSON Output", lines=15)],
    title="Project Nexus - Test Backend (on Render)",
    description="This is a dummy backend. It receives a prompt and always returns the same hard-coded JSON training plan."
)

# --- Flask Web Server ---
# Render needs a standard web server. We will use Flask to wrap our Gradio app.
app = Flask(__name__)

# This mounts the Gradio app onto the Flask server, making it accessible.
app = gr.mount_gradio_app(app, demo, path="/")

# This part is for Render to run the app using a production server (gunicorn).
if __name__ == "__main__":
    # This line is for local testing only and will not be used by Render.
    app.run()
