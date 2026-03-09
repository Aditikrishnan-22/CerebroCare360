from flask import render_template, request
from flask_login import login_required
from app.blueprints.hospital import hospital_bp
from app.models.hospital import Hospital


@hospital_bp.route('/find')
@login_required
def find():
    tab       = request.args.get('tab', 'hospitals')
    state     = request.args.get('state', '').strip()
    city      = request.args.get('city', '').strip()
    specialty = request.args.get('specialty', '').strip()
    h_type    = request.args.get('hospital_type', '').strip()
    rating    = request.args.get('rating', '').strip()

    query = Hospital.query.filter_by(is_active=True)

    # MRI tab — only show MRI centres
    if tab == 'mri':
        query = query.filter_by(is_mri_center=True)
    else:
        # Hospitals tab — exclude pure clinics if no filter applied
        pass

    if state:
        query = query.filter(Hospital.state.ilike(f'%{state}%'))
    if city:
        query = query.filter(Hospital.city.ilike(f'%{city}%'))
    if specialty and tab != 'mri':
        query = query.filter(Hospital.specialty.ilike(f'%{specialty}%'))
    if h_type:
        query = query.filter(Hospital.hospital_type.ilike(f'%{h_type}%'))
    if rating:
        try:
            query = query.filter(Hospital.rating >= float(rating))
        except ValueError:
            pass

    hospitals = query.order_by(Hospital.rating.desc()).all()
    return render_template('hospital/find.html', hospitals=hospitals, tab=tab)


@hospital_bp.route('/<int:hospital_id>')
@login_required
def detail(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    return render_template('hospital/detail.html', hospital=hospital)