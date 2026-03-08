from flask import render_template, request
from flask_login import login_required
from app.blueprints.symptom import symptom_bp
from app.models.symptom_rule import SymptomRule
import json

@symptom_bp.route('/checker', methods=['GET', 'POST'])
@login_required
def checker():
    result = None
    selected_symptoms = []

    if request.method == 'POST':
        selected_symptoms = request.form.getlist('symptoms')
        if selected_symptoms:
            rules = SymptomRule.query.all()
            best_match = None
            best_score = 0
            for rule in rules:
                try:
                    rule_keys = json.loads(rule.symptom_keys)
                except Exception:
                    rule_keys = []
                matches = len(set(selected_symptoms) & set(rule_keys))
                if matches > best_score:
                    best_score = matches
                    best_match = rule
            if best_match and best_score > 0:
                result = {
                    'condition':  best_match.condition,
                    'department': best_match.department,
                    'urgency':    best_match.urgency,
                    'advice':     best_match.advice
                }
            else:
                result = {
                    'condition':  'General Assessment Needed',
                    'department': 'General Medicine',
                    'urgency':    'low',
                    'advice':     'Your symptoms do not match a specific pattern. Please consult a general physician.'
                }

    return render_template('symptom/checker.html',
                           result=result,
                           selected_symptoms=selected_symptoms)