import os

import google.generativeai as genai
from flask import Blueprint, jsonify, request, session

from models.db import execute_query

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'reply': 'Please enter a message.'}), 400

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'reply': 'Chat is not configured (missing API key).'}), 503

    is_admin = session.get('admin_logged_in', False)

    if is_admin:
        inventory = execute_query('SELECT blood_type, units FROM blood_inventory ORDER BY blood_type')
        donor_count = execute_query('SELECT COUNT(*) AS cnt FROM donors')[0]['cnt']
        pending = execute_query(
            "SELECT COUNT(*) AS cnt FROM blood_requests WHERE status='pending'"
        )[0]['cnt']
        hospital_count = execute_query('SELECT COUNT(*) AS cnt FROM hospitals')[0]['cnt']
        low_stock = execute_query('SELECT blood_type, units FROM blood_inventory WHERE units < 5')

        inv_lines = '\n'.join(f"  {r['blood_type']}: {r['units']} units" for r in inventory)
        low_names = ', '.join(f"{r['blood_type']} ({r['units']})" for r in low_stock) or 'None'

        system = (
            "You are an admin assistant for a blood bank management system.\n"
            f"Current live data:\n"
            f"- Total donors: {donor_count}\n"
            f"- Pending blood requests: {pending}\n"
            f"- Registered hospitals: {hospital_count}\n"
            f"- Blood inventory:\n{inv_lines}\n"
            f"- Low stock (< 5 units): {low_names}\n\n"
            "Answer staff questions about inventory, donors, and requests concisely. "
            "If asked to perform actions (approve requests, add donors), explain they must use the app interface."
        )
    else:
        system = (
            "You are a helpful assistant for a blood bank. Help donors and visitors with:\n"
            "- Donation eligibility: must be 18-65 years old, weight > 50 kg, healthy, "
            "and at least 90 days since last whole-blood donation.\n"
            "- Blood type information and compatibility.\n"
            "- The donation process and what to expect.\n"
            "- General blood bank FAQs.\n\n"
            "Be friendly and concise. For medical advice beyond general eligibility, recommend consulting a doctor. "
            "Never share or speculate about personal donor data."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system,
        )
        response = model.generate_content(message)
        reply = response.text
    except Exception as e:
        reply = f'Sorry, the assistant is temporarily unavailable. ({e})'

    return jsonify({'reply': reply})
