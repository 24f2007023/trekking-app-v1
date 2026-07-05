from flask import Blueprint, render_template

from decorators import role_required

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@role_required('trekker')
def dashboard():
    return render_template('user/dashboard.html')
