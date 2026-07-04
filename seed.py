from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app, db
from models import Trek, User

ADMIN_EMAIL = 'admin@trekking.com'
ADMIN_PASSWORD = 'Admin@123'

SAMPLE_TREKS = [
    dict(name='Everest Base Camp', location='Nepal', difficulty='Hard', duration_days=12,
         available_slots=10, status='Open', start_date=date(2026, 5, 20), end_date=date(2026, 5, 31),
         description='A classic high-altitude trek to the base of Mount Everest.'),
    dict(name='Roopkund Trek', location='Uttarakhand', difficulty='Moderate', duration_days=7,
         available_slots=15, status='Open', start_date=date(2026, 5, 10), end_date=date(2026, 5, 16),
         description='A high-altitude glacial lake trek in the Himalayas.'),
    dict(name='Kedarkantha Trek', location='Uttarakhand', difficulty='Easy', duration_days=6,
         available_slots=20, status='Closed', start_date=date(2026, 4, 1), end_date=date(2026, 4, 6),
         description='A popular winter trek known for panoramic Himalayan views.'),
    dict(name='Hampta Pass', location='Himachal Pradesh', difficulty='Moderate', duration_days=5,
         available_slots=12, status='Pending', start_date=date(2026, 6, 12), end_date=date(2026, 6, 16),
         description='A crossover trek from lush green valleys to the arid Lahaul region.'),
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            admin = User(
                name='Admin',
                email=ADMIN_EMAIL,
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                role='admin',
            )
            db.session.add(admin)

        if Trek.query.count() == 0:
            for trek_data in SAMPLE_TREKS:
                db.session.add(Trek(**trek_data))

        db.session.commit()
        print('Database initialized and seeded.')


if __name__ == '__main__':
    seed()
