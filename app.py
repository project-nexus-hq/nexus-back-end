import gradio as gr
import json

def generate_dummy_plan(user_prompt):
    print(f"Received prompt from user: {user_prompt}") 
    dummy_plan = [
        {"step_number": 1, "title": "CompTIA Network+ Certification", "justification": "This is the foundational step.", "url": "https://www.comptia.org/certifications/network"},
        {"step_number": 2, "title": "Introduction to Python for Automation", "justification": "Learning a scripting language is critical.", "url": "https://www.udemy.com/course/python-for-network-engineers/"},
        {"step_number": 3, "title": "Hands-On Red Team Tactics", "justification": "Now you can begin to apply offensive security techniques.", "url": "https://www.oreilly.com/library/view/red-team-development/9781492044369/"}
    ]
    return json.dumps(dummy_plan, indent=2)

# THE ONLY CHANGE: Remove the square brackets [] from inputs and outputs.
app = gr.Interface(
    fn=generate_dummy_plan,
    inputs=gr.Textbox(label="User Prompt", lines=4),
    outputs=gr.Textbox(label="Generated JSON Output", lines=15),
    title="Project Nexus - Test Backend (on Render)"
)

# This block allows Gunicorn to find and run the Gradio app.
if __name__ == "__main__":
    app.launch()
