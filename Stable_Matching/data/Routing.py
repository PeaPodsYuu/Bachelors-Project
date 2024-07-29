import os

import bcrypt
from flask import request, render_template, make_response, redirect, url_for, send_from_directory
from flask_wtf import FlaskForm
from wtforms import validators
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, PasswordField, TextAreaField, SubmitField

from data.classes import User, Project
from data.comments import comments
from data.flask_app import app, db, domain
from data.constants.specialization_constants import SpecializationConstants
from data.constants.skill_level_constants import SkillLevelConstants
from data.project_connectors import project_connectors
from data.matching import perform_match

# User routes
class RegistrationForm(FlaskForm):
    class Meta:
        csrf = False

    username = StringField('Username', [
        validators.Length(min=4, max=32, message="Your username must be between 4 and 32 characters long."),
        validators.InputRequired(message="Please enter your username.")
    ])

    email = StringField('Email Address', [
        validators.Email(message="Please enter a valid email address\nEx.: John_Doe@hotmail.com"),
        validators.Length(min=6, max=128, message="Your password must be between 6 and 128 characters long."),
        validators.InputRequired(message="Please enter your email address.")
    ])

    password = PasswordField('Password', [
        validators.Length(min=6, max=64, message="Your password must be between 6 and 32 characters long."),
        validators.InputRequired(message="Please enter your password.")
    ])

    confirm = PasswordField('Repeat Password', [
        validators.Length(min=6, max=64, message="Your password must be between 6 and 32 characters long."),
        validators.EqualTo('password', message="Passwords must match."),
        validators.InputRequired(message="Please re-enter your password.")
    ])

    def validate(self, extra_validators=None):
        initial_validation = super(RegistrationForm, self).validate(extra_validators)
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('User already exists')
            return False
        return True


class LoginForm(FlaskForm):
    class Meta:
        csrf = False

    username = StringField('Username', validators=[
        validators.Length(min=4, max=32, message="Your username must be between 4 and 32 characters long."),
        validators.InputRequired(message="Please enter your username.")
    ])
    password = PasswordField('Password', validators=[
        validators.Length(min=6, max=32, message="Your password must be between 6 and 32 characters long."),
        validators.InputRequired(message="Please enter your password.")
    ])

    def validate(self, extra_validators=None):
        initial_validation = super(LoginForm, self).validate(extra_validators)
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if not user:
            self.username.errors.append('Unknown username')
            return False
        if not user.verify_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        return True

class SpecForm(FlaskForm):
    class Meta:
        csrf = False

    enum_repr = SpecializationConstants.__members__
    choices_spec = [(None, None)]
    for enum in enum_repr:
        choices_spec.append((enum, SpecializationConstants.get_specialization_name(enum)))

    enum_repr = SkillLevelConstants.__members__
    choices_skill = [(None, None)]
    for enum in enum_repr:
        choices_skill.append((enum, SkillLevelConstants.get_skill_level_name(enum)))

    specialization = SelectField('Specialization', choices=choices_spec)
    level = SelectField('Qualification Level', choices=choices_skill)


@app.route('/register', methods=['GET', 'POST'])
def register_new_user():
    User.set_connected_user_by_current_cookie()

    if User.connected_user:
        return redirect(url_for('display_landing_page'))

    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        salt = bcrypt.gensalt()
        user = User(form.username.data, bcrypt.hashpw(str.encode(form.password.data), salt),
                    form.email.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login_user'))
    return render_template('register_page.html', form=form, current_user=None)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    User.set_connected_user_by_current_cookie()

    if User.connected_user:
        return redirect(url_for('display_landing_page'))

    print(User.connected_user)
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        resp = make_response(redirect(url_for('display_landing_page')))

        salt = bcrypt.gensalt()
        encrypted_id = bcrypt.hashpw(str.encode(str(user.id)), salt)

        resp.set_cookie(key='uid', value=str(encrypted_id), domain=domain)
        redirect(url_for("getcookie"))
        return resp
    return render_template('login_page.html', form=form, current_user=None)


@app.route('/logout', methods=['GET', 'POST'])
def logout_user():
    User.connected_user = None
    resp = make_response(redirect(url_for('display_landing_page')))
    resp.delete_cookie(key='uid', domain=domain)
    return resp


@app.route('/remove_specialization/<name>/<spec>', methods=['GET'])
def remove_spec(name, spec):
    current_user = User.set_connected_user_by_current_cookie()
    if not current_user:
        return redirect(url_for('display_landing_page'))

    user = User.get_user_by_name(name)
    user.remove_specialization(spec)

    return redirect(url_for('display_profile', name=user.username))


@app.route('/remove_specialization_project/<id>/<spec>', methods=['GET'])
def remove_spec_project(id, spec):
    current_user = User.set_connected_user_by_current_cookie()
    if not current_user:
        return redirect(url_for('display_landing_page'))

    project = Project.get(id)
    project.remove_specialization(spec)

    return redirect(url_for('display_project', proj_id=project.id))


@app.route('/profile/<name>', methods=['GET'])
def display_profile(name):
    User.set_connected_user_by_current_cookie()
    user = User.query.filter_by(username=name).first()
    if not user:
        return redirect(url_for('display_landing_page'))

    projects_owned = user.get_projects_owned()
    projects_joined = user.get_projects_joined()
    specializations = user.get_specializations()

    form = SpecForm(request.form)
    args = []
    for arg in request.args.values():
        args.append(arg)
    if (request.method == 'GET' and len(args) > 0 and args[0] != 'None' and args[1] != 'None'
            and SpecializationConstants.get_specialization_name(args[0]) not in user.get_specializations()
            and SpecializationConstants.get_specialization_name(args[0]) != "NOT A SPECIALIZATION NAME"):
        print("Adding", args[0], args[1], type(args[0]), args[0] == 'None')

        user.add_specialization(args[0], args[1])

        for _arg in args:
            _arg = None
        resp = make_response(redirect(url_for('display_profile', name=user.username)))
        return resp

    return render_template('profile_page.html', user=user, current_user=User.connected_user, projects_owned=projects_owned, projects_joined=projects_joined, specializations=specializations, form=form)


@app.route('/setcookie', methods=['GET', 'POST'])
def setcookie():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        resp = make_response(redirect(url_for('display_landing_page')))
        resp.set_cookie(key='uid', value=str(user.id), domain=domain)
        print(getcookie('uid'))
        return resp


@app.route('/getcookie')
def getcookie():
    resp = make_response(request.cookies.get('uid'))

    return resp


# Project routes

class ProjectCreationForm(FlaskForm):
    class Meta:
        csrf = False

    name = StringField('Project Name', [
        validators.Length(min=4, max=64, message="Your project's name must be between 4 and 64 characters long."),
        validators.InputRequired(message="Please enter your project's name.")
    ])

    description = TextAreaField('Project Description', [
        validators.Length(min=6, max=2048,
                          message="Your project description must be between 6 and 2048 characters long."),
        validators.InputRequired(message="Please enter your project's description."),
    ])

    def validate(self, extra_validators=None):
        initial_validation = super(ProjectCreationForm, self).validate(extra_validators)
        if not initial_validation:
            return False
        project = Project.query.filter_by(name=self.name.data).first()
        if project:
            self.name.errors.append('Project with the same name already exists')
            return False
        return True


class CommentForm(FlaskForm):
    class Meta:
        csrf = False

    comment = TextAreaField('Post A Comment', [
        validators.Length(min=1, max=2048,
                          message="Comment must be between 1 and 2048 characters."),
        validators.InputRequired(message="Please enter a comment."),
    ])

    def validate(self, extra_validators=None):
        initial_validation = super(CommentForm, self).validate(extra_validators)
        if not initial_validation:
            return False
        comment = comments.query.filter_by(comment=self.comment.data).first()
        if comment:
            self.comment.errors.append('To prevent spam, you may not post the same comment as another user.')
            return False
        return True

@app.route('/project/<int:proj_id>', methods=['GET', 'POST'])
def display_project(proj_id):
    current_user = User.set_connected_user_by_current_cookie()
    project = Project.query.filter_by(id=proj_id).first()
    if not project:
        return redirect(url_for('display_landing_page'))

    users_in_project = db.session.query(project_connectors).filter_by(project_id=proj_id).all()
    comments_in_project = db.session.query(comments).filter_by(project_id=proj_id).all()
    members = []
    owner = None
    for connector in users_in_project:
        if connector.relation == 'Owner':
            owner = User.get(connector.user_id)
        elif connector.relation == 'Member':
            members.append(User.get(connector.user_id))

    comment_form = CommentForm(request.form)
    if request.method == 'POST' and comment_form.validate():
        comment = comments(user=current_user.username, project_id=proj_id, comment=comment_form.comment.data)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for(f'display_project', proj_id=proj_id, owner=owner, members=members, current_user=current_user, comments_in_project=comments_in_project, comment_form=comment_form, comment=comment))

    spec_form = SpecForm(request.form)
    args = []
    for arg in request.args.values():
        args.append(arg)
    if (request.method == 'GET' and len(args) > 0 and args[0] != 'None'
            and SpecializationConstants.get_specialization_name(args[0]) not in project.get_specializations()
            and SpecializationConstants.get_specialization_name(args[0]) != "NOT A SPECIALIZATION NAME"):
        project.add_specialization(args[0])

        for _arg in args:
            _arg = None
        resp = make_response(redirect(url_for('display_project', proj_id=project.id)))
        return resp
    return render_template('project.html', project=project, owner=owner, members=members,
                           current_user=current_user, comments_in_project=comments_in_project, comment_form=comment_form,
                           spec_form=spec_form, specializations=project.get_specializations())


@app.route('/create_project', methods=['GET', 'POST'])
def create_new_project():
    current_user = User.set_connected_user_by_current_cookie()
    if not current_user:
        return redirect(url_for('display_landing_page'))

    form = ProjectCreationForm(request.form)
    if request.method == 'POST' and form.validate():
        project = Project(form.name.data, form.description.data)
        db.session.add(project)
        db.session.commit()

        project_link = project_connectors(User.connected_user.id, project.id, "Owner")
        db.session.add(project_link)
        db.session.commit()
        return redirect(url_for(f'display_project', proj_id=project.id))
    return render_template('create_project_page.html', form=form, current_user=User.connected_user)


@app.route('/project/<int:proj_id>/add_comment', methods=['GET', 'POST'])
def add_comment_to_project(proj_id):
    current_user = User.set_connected_user_by_current_cookie()
    if not current_user:
        return redirect(url_for('display_landing_page'))

    form = CommentForm(request.form)
    if request.method == 'POST' and form.validate():
        comment = comments(user_id=current_user.id, project_id=proj_id, comment=form.comment)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for(f'display_project', proj_id=proj_id))
    return render_template('create_project_page.html', form=form, current_user=User.connected_user)


@app.route('/projects')
def display_projects_page(content=None):
    current_user = User.set_connected_user_by_current_cookie()
    return render_template('project_browser.html', current_user=current_user, projects=Project.query.all())

@app.route('/project/apply/<user_id>/<project_id>', methods=["POST"])
def apply_to_project(user_id, project_id):
    current_user = User.set_connected_user_by_current_cookie()
    got_user = User.get(user_id)
    if current_user != got_user:
        redirect(url_for('display_landing_page'))

    got_project = Project.get(project_id)
    got_project.add_user_application(got_user)
    return redirect(url_for('display_project', proj_id=got_project.id))

@app.route('/perform_matching')
def perform_matching():
    current_user = User.set_connected_user_by_current_cookie()
    if current_user.is_admin == "True":
        perform_match()
    return redirect(url_for('display_landing_page'))