from flask import Blueprint, render_template

from decorators import role_required

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


@staff_bp.route('/dashboard')
@role_required('staff')
def dashboard():
    return render_template('staff/dashboard.html')
