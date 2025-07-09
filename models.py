from app import db
from datetime import datetime

class Regulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_level = db.Column(db.String(50), nullable=False)  # National, State, Local
    location = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    key_requirements = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Legal')  # Legal, Licensing, Taxes, Zoning, Occupancy, Registration, Discrimination
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Regulation {self.title}>'

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    jurisdiction_affected = db.Column(db.String(100), nullable=False)
    update_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Recent, Upcoming, Proposed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Update {self.title}>'

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<AdminUser {self.username}>'
