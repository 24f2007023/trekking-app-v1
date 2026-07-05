import os

from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'trekking.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key'

    db.init_app(app)

    from auth import auth_bp
    from admin import admin_bp
    from staff import staff_bp
    from user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    @app.route('/')
    def index():
        role = session.get('role')
        if role in ('admin', 'staff', 'trekker'):
            endpoint = {'admin': 'admin.dashboard', 'staff': 'staff.dashboard', 'trekker': 'user.dashboard'}[role]
            return redirect(url_for(endpoint))
        return redirect(url_for('auth.login'))

    return app
