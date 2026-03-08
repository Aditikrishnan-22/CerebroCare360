from flask import render_template, request, jsonify
from flask_login import login_required
from app.blueprints.chat import chat_bp
from flask import current_app
from groq import Groq

SYSTEM_PROMPT = """You are CerebroBot, a helpful medical information assistant 
for CerebroCare360 — an AI-powered brain tumor detection platform.

You help users understand:
- Brain tumor types: Glioma, Meningioma, Pituitary tumors
- What MRI scans are and how they work
- How to interpret their CerebroCare360 results
- General symptoms associated with brain tumors
- When to seek medical attention
- How to use the CerebroCare360 platform

Important rules:
- Always remind users you are NOT a doctor and cannot provide medical diagnosis
- Always encourage users to consult a qualified neurologist for medical decisions
- Be empathetic, clear, and supportive
- Keep responses concise and easy to understand
- If asked about something unrelated to brain health or the platform, politely redirect
- Never cause unnecessary panic — be calm and factual"""


@chat_bp.route('/chat')
@login_required
def index():
    return render_template('chat/index.html')


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send():
    data     = request.get_json()
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])

        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',   # free, fast, good quality
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                *messages
            ],
            max_tokens=600,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500