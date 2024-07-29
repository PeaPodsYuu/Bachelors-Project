from data.flask_app import db


class ProjectSpecializations(db.Model):
    project_id = db.Column(db.Integer, primary_key=True)
    specialization = db.Column(db.String(64), primary_key=True)

    def __init__(self, project_id, specialization):
        self.project_id = project_id
        self.specialization = specialization