from flask import render_template, request
from flask_login import login_required
from app.blueprints.hospital import hospital_bp
from app.models.hospital import Hospital

@hospital_bp.route('/find')
@login_required
def find():
    state     = request.args.get('state', '').strip()
    city      = request.args.get('city', '').strip()
    specialty = request.args.get('specialty', '').strip()
    h_type    = request.args.get('hospital_type', '').strip()
    rating    = request.args.get('rating', '').strip()

    query = Hospital.query.filter_by(is_active=True)
    if state:
        query = query.filter(Hospital.state.ilike(f'%{state}%'))
    if city:
        query = query.filter(Hospital.city.ilike(f'%{city}%'))
    if specialty:
        query = query.filter(Hospital.specialty.ilike(f'%{specialty}%'))
    if h_type:
        query = query.filter(Hospital.hospital_type.ilike(f'%{h_type}%'))
    if rating:
        try:
            r_val = float(rating)
            query = query.filter(Hospital.rating >= r_val)
        except ValueError:
            pass

    hospitals = query.all()
    return render_template('hospital/find.html', hospitals=hospitals)