# Used for bridging users and projects
from data.flask_app import db


class project_connectors(db.Model):
    __tablename__ = 'project_connectors'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    relation = db.Column(db.String())

    def __init__(self, user_id, project_id, relation):
        self.user_id = user_id
        self.project_id = project_id
        self.relation = relation