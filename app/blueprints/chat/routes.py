from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.chat import chat_bp
from flask import current_app
from groq import Groq
from app.models.mri_scan import MRIScan
from app.models.chat_session import ChatSession, ChatMessage
from app.extensions import db


def build_system_prompt(all_scans):
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
- If asked to look at or analyse a scan image, clarify you cannot see images but CAN
  discuss the result data provided below.
- You CAN reference any scan by its Scan ID when the user asks about it.
"""

    if not all_scans:
        base += "\nUSER SCAN HISTORY: This user has not uploaded any MRI scans yet.\n"
        return base

    base += f"\nUSER SCAN HISTORY ({len(all_scans)} total scans — reference any by Scan ID):\n"
    base += "-" * 60 + "\n"

    for scan in all_scans:
        p        = scan.prediction
        date_str = scan.upload_date.strftime('%d %b %Y') if scan.upload_date else 'Unknown'

        if not p:
            base += f"Scan ID #{scan.id} | Date: {date_str} | Status: No prediction yet\n"
            continue

        if p.has_tumor:
            result_str = f"TUMOR DETECTED — {p.tumor_type.capitalize() if p.tumor_type else 'Unknown'}"
            probs = (f"Glioma={p.prob_glioma*100:.1f}% "
                     f"Meningioma={p.prob_meningioma*100:.1f}% "
                     f"Pituitary={p.prob_pituitary*100:.1f}% "
                     f"NoTumor={p.prob_notumor*100:.1f}%")
        else:
            result_str = "NO TUMOR DETECTED"
            probs = (f"NoTumor={p.prob_notumor*100:.1f}% "
                     f"Glioma={p.prob_glioma*100:.1f}% "
                     f"Meningioma={p.prob_meningioma*100:.1f}% "
                     f"Pituitary={p.prob_pituitary*100:.1f}%")

        base += (f"Scan ID #{scan.id} | Date: {date_str} | Result: {result_str} | "
                 f"Confidence: {p.confidence*100:.1f}% | Probs: {probs} | "
                 f"Model: {p.model_version}\n")

    base += "-" * 60 + "\n"
    base += (f"When the user asks about a specific scan (e.g. 'scan 5', 'my second scan'), "
             f"refer to the matching Scan ID above and discuss that result specifically.\n"
             f"The LATEST scan is Scan ID #{all_scans[0].id}.\n")

    return base


@chat_bp.route('/chat')
@login_required
def index():
    # New session per page visit
    session = ChatSession(user_id=current_user.id)
    db.session.add(session)
    db.session.commit()

    latest_scan = (MRIScan.query
                   .filter_by(user_id=current_user.id)
                   .order_by(MRIScan.upload_date.desc())
                   .first())

    return render_template(
        'chat/index.html',
        session_id=session.id,
        latest_scan=latest_scan,
        latest_prediction=latest_scan.prediction if latest_scan else None
    )


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send():
    data       = request.get_json()
    user_msg   = data.get('message', '').strip()
    session_id = data.get('session_id')

    if not user_msg:
        return jsonify({'error': 'Empty message'}), 400

    session = ChatSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first()

    if not session:
        return jsonify({'error': 'Invalid session'}), 400

    # Save user message
    db.session.add(ChatMessage(session_id=session.id, role='user', content=user_msg))
    db.session.commit()

    # Last 10 messages chronologically
    recent = (ChatMessage.query
              .filter_by(session_id=session.id)
              .order_by(ChatMessage.created_at.desc())
              .limit(10)
              .all())
    recent = list(reversed(recent))

    groq_messages = [{'role': m.role, 'content': m.content} for m in recent]

    # All user scans for system prompt
    all_scans = (MRIScan.query
                 .filter_by(user_id=current_user.id)
                 .order_by(MRIScan.upload_date.desc())
                 .all())

    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])
        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {'role': 'system', 'content': build_system_prompt(all_scans)},
                *groq_messages
            ],
            max_tokens=600,
            temperature=0.7
        )
        reply = response.choices[0].message.content

        # Save bot reply
        db.session.add(ChatMessage(session_id=session.id, role='assistant', content=reply))
        db.session.commit()

        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500