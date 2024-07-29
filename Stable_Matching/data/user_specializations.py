from data.flask_app import db


class UserSpecializations(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    specialization = db.Column(db.String(64), primary_key=True)
    level = db.Column(db.Integer())

    def __init__(self, user_id, specialization, level):
        self.user_id = user_id
        self.specialization = specialization
        self.level = level