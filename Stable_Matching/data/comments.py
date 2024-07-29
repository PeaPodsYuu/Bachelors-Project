from data.flask_app import db


class comments(db.Model):
    __tablename__ = 'comments'

    user = db.Column(db.String(), db.ForeignKey('user.username'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    comment = db.Column(db.String(), primary_key=True)

    def __init__(self, user, project_id, comment):
        self.user = user
        self.project_id = project_id
        self.comment = comment