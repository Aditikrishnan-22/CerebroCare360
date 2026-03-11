from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.chat import chat_bp
from flask import current_app
from groq import Groq
from app.models.mri_scan import MRIScan
from app.models.prediction import Prediction


def build_system_prompt(scan_context: dict = None) -> str:
    base = """You are CerebroBot, a helpful medical information assistant
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
- Never cause unnecessary panic — be calm and factual

CRITICAL — IMAGE ACCESS LIMITATION:
- You CANNOT see or analyse any MRI scan image. You do NOT have image-viewing capability.
- If a user asks you to "look at", "check", or "analyse" their scan image, clearly explain
  you cannot see images, but you CAN discuss the result data the platform has shared with you.
- Never pretend to analyse an image. Direct users to their Results page for visual output.
"""

    if not scan_context or not scan_context.get('hasScan'):
        base += """
USER SCAN STATUS: This user has not uploaded any MRI scan yet.
If they ask about results, guide them to upload a scan first.
"""
        return base

    has_tumor   = scan_context.get('hasTumor', False)
    tumor_type  = scan_context.get('tumorType', 'Unknown')
    confidence  = scan_context.get('confidence', 0)
    scan_date   = scan_context.get('scanDate', '')
    p_glioma    = scan_context.get('probGlioma', 0)
    p_mening    = scan_context.get('probMeningioma', 0)
    p_pituitary = scan_context.get('probPituitary', 0)
    p_notumor   = scan_context.get('probNotumor', 0)

    result_str = f"Tumor detected — {tumor_type}" if has_tumor else "No tumor detected"
    conf_note  = (
        f"High confidence ({confidence}%) — but always stress AI results are not a clinical diagnosis."
        if confidence >= 75 else
        f"Moderate confidence ({confidence}%) — emphasise the importance of specialist review."
    )
    edu_note = (
        f"Explain what {tumor_type} means educationally, typical symptoms, and that specialist review is essential."
        if has_tumor else
        "Reassure the user appropriately. Note that a clear result does not rule out all conditions — "
        "if they have symptoms, they should still see a neurologist."
    )

    base += f"""
USER'S LATEST SCAN RESULT (from the platform AI model — you did NOT see the image):
- Scan date: {scan_date}
- Result: {result_str}
- Confidence: {confidence}%
- Class probabilities: Glioma {p_glioma}% | Meningioma {p_mening}% | Pituitary {p_pituitary}% | No Tumor {p_notumor}%

When discussing this result:
- Make clear this data came from the CerebroCare360 AI model, not from you viewing the scan.
- {edu_note}
- {conf_note}
"""
    return base


@chat_bp.route('/chat')
@login_required
def index():
    latest_scan = (MRIScan.query
                   .filter_by(user_id=current_user.id)
                   .order_by(MRIScan.upload_date.desc())
                   .first())

    latest_prediction = None
    if latest_scan:
        latest_prediction = (Prediction.query
                             .filter_by(scan_id=latest_scan.id)
                             .filter(Prediction.model_version != 'pending')
                             .first())

    return render_template(
        'chat/index.html',
        latest_scan=latest_scan,
        latest_prediction=latest_prediction
    )


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send():
    data         = request.get_json()
    messages     = data.get('messages', [])
    scan_context = data.get('scan_context', {})

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])

        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {'role': 'system', 'content': build_system_prompt(scan_context)},
                *messages
            ],
            max_tokens=600,
            temperature=0.7
        )

        reply = response.choices[0].message.content
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500