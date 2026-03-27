import gradio as gr
import json
import os # <--- CHANGE 1: Import the 'os' library

# The rest of the function is the same
def generate_dummy_plan(user_prompt):
    print(f"Received prompt from user: {user_prompt}") 

    dummy_plan = [
        {"step_number": 1, "title": "CompTIA Network+ Certification", "justification": "This is the foundational step.", "url": "https://www.comptia.org/certifications/network"},
        {"step_number": 2, "title": "Introduction to Python for Automation", "justification": "Learning a scripting language is critical.", "url": "https://www.udemy.com/course/python-for-network-engineers/"},
        {"step_number": 3, "title": "Hands-On Red Team Tactics", "justification": "Now you can begin to apply offensive security techniques.", "url": "https://www.oreilly.com/library/view/red-team-development/9781492044369/"}
    ]
    
    return json.dumps(dummy_plan, indent=2)

demo = gr.Interface(
    fn=generate_dummy_plan,
    inputs=[gr.Textbox(label="User Prompt", lines=4)],
    outputs=[gr.Textbox(label="Generated JSON Output", lines=15)],
    title="Project Nexus - Test Backend (on Render)"
)

# --- CHANGE 2: The updated launch command ---
# It now reads the PORT environment variable provided by Render.
# The 'int()' converts the port from a string to a number.
# It defaults to 7860 if the PORT variable isn't found (for local testing).
demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get('PORT', 7860)))
