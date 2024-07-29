import bcrypt
from flask import request
from flask_login import UserMixin

from data.constants.skill_level_constants import SkillLevelConstants
from data.constants.specialization_constants import SpecializationConstants
from data.flask_app import db, login_manager
from data.project_connectors import project_connectors
from data.project_specializations import ProjectSpecializations
from data.user_specializations import UserSpecializations


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32))
    password = db.Column(db.String(64))
    email = db.Column(db.String(128))
    is_admin = db.Column(db.String(6))

    connected_user = None

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def __repr__(self):
        return f"User: {self.username}\nEmail: {self.email}"

    def verify_password(self, password):
        return bcrypt.checkpw(str.encode(password), self.password)

    @classmethod
    def get_user_id_by_encrypted_id(cls, encrypted_id):
        """Will utilize an encrypted ID to return a decrypted id"""
        if encrypted_id:
            encrypted_id = encrypted_id[2:len(encrypted_id) - 1]
            for user in User.query.all():
                if bcrypt.checkpw(str(user.id).encode(), encrypted_id.encode()):
                    return user.id
        else:
            return 0

    @classmethod
    def get_user_by_name(cls, name):
        return User.query.filter_by(username=name).first()

    @classmethod
    def get(cls, uid):
        """Generic user getter by id"""
        return User.query.get(uid)

    @classmethod
    def set_connected_user(cls, user):
        """Sets the connected user in order to prevent access to certain pages, and handle cookies"""
        cls.connected_user = user

    @classmethod
    def set_connected_user_by_current_cookie(cls):
        """Sets the connected user by cookie"""
        cls.set_connected_user(load_user(cls.get_user_id_by_encrypted_id(request.cookies.get('uid'))))
        return cls.connected_user

    def get_projects_owned(self):
        """Get all the projects owned by the user"""
        projects = []
        for connector in project_connectors.query.all():
            if connector.user_id == self.id and connector.relation == "Owner":
                projects.append(Project.get(connector.project_id))
        return projects

    def get_projects_joined(self):
        """Get all the projects the user is part of, but does not own"""
        projects = []
        for connector in project_connectors.query.all():
            if connector.user_id == self.id and connector.relation == "Member":
                projects.append(Project.get(connector.project_id))
        return projects

    def get_specializations(self):
        """Get all the specializations of the user in the form {specialization : skill}"""
        specializations = {}
        specs = UserSpecializations.query.filter_by(user_id=self.id).all()
        for spec in specs:
            specializations[SpecializationConstants.get_specialization_name(spec.specialization)] = \
                SkillLevelConstants.get_skill_level_name(spec.level)
        return specializations

    def add_specialization(self, specialization, level):
        """Add a new specialization to the user"""
        db.session.add(UserSpecializations(self.id, specialization, level))
        db.session.commit()

    def remove_specialization(self, specialization):
        """Remove a specialization"""
        for spec in SpecializationConstants.__members__:
            if specialization == SpecializationConstants.get_specialization_name(spec):
                specialization = SpecializationConstants.__members__.get(spec)
                break
        specialization = str(specialization).split('.')[-1]

        spec_to_remove = UserSpecializations.query.filter_by(user_id=self.id, specialization=specialization).first()
        db.session.query(UserSpecializations).filter(UserSpecializations.user_id == self.id,
                                                     UserSpecializations.specialization == spec_to_remove.specialization).delete()
        db.session.commit()

    def is_user_applying_to_project(self, project):
        """Check if a user is applying to the project"""
        is_user_applicant = False
        for connector in project_connectors.query.all():
            if connector.user_id == self.id and connector.relation == "Applicant":
                is_user_applicant = True
                break
        return is_user_applicant



class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(2048))

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        to_print = f"Project Name: {self.name}"
        if self.description != "":
            to_print += f"\nDescription: {self.description}"
        return to_print

    @classmethod
    def get(cls, id):
        """Generic return method for a project by id"""
        return Project.query.get(id)


    def get_specializations(self):
        """Get all the specializations the project requires in the form [specialization, ...]"""
        specs = [SpecializationConstants.get_specialization_name(x.specialization)
                 for x in ProjectSpecializations.query.filter_by(project_id=self.id).all()]
        return specs

    def add_specialization(self, specialization):
        """Add a new specialization to the project"""
        db.session.add(ProjectSpecializations(self.id, specialization))
        db.session.commit()

    def remove_specialization(self, specialization):
        """Remove a specialization"""
        for spec in SpecializationConstants.__members__:
            if specialization == SpecializationConstants.get_specialization_name(spec):
                specialization = SpecializationConstants.__members__.get(spec)
                break
        specialization = str(specialization).split('.')[-1]

        spec_to_remove = ProjectSpecializations.query.filter_by(project_id=self.id, specialization=specialization).first()
        db.session.query(ProjectSpecializations).filter(ProjectSpecializations.project_id == self.id,
                                                     ProjectSpecializations.specialization == spec_to_remove.specialization).delete()
        db.session.commit()

    def add_user_application(self, user):
        """Adds the application of a user to the database"""
        db.session.add(project_connectors(user.id, self.id, 'Applicant'))
        db.session.commit()


    def accept_user_application(self, user):
        """Accepts the application of a user by removing applicant status and adding member status"""
        is_user_applicant = False
        for connector in project_connectors.query.all():
            if connector.user_id == user.id and connector.relation == "Applicant":
                is_user_applicant = True
                break
        if is_user_applicant:
            relation_to_remove = project_connectors.query.filter_by(user_id=user.id, project_id=self.id).first()
            db.session.query(project_connectors).filter(project_connectors.user_id == relation_to_remove.user_id,
                                                         project_connectors.project_id == relation_to_remove.project_id).delete()
            db.session.add(project_connectors(user.id, self.id, 'Member'))
            db.session.commit()
