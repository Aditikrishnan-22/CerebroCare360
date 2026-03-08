from flask import render_template, request
from flask_login import login_required
from app.blueprints.hospital import hospital_bp
from app.models.hospital import Hospital

@hospital_bp.route('/find')
@login_required
def find():
    city      = request.args.get('city', '').strip()
    specialty = request.args.get('specialty', '').strip()

    query = Hospital.query.filter_by(is_active=True)
    if city:
        query = query.filter(Hospital.city.ilike(f'%{city}%'))
    if specialty:
        query = query.filter(Hospital.specialty.ilike(f'%{specialty}%'))

    hospitals = query.all()
    return render_template('hospital/find.html', hospitals=hospitals)