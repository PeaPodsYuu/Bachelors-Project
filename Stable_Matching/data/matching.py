from data.classes import Project, User
from data.project_connectors import project_connectors
from data.constants.specialization_constants import SpecializationConstants
from data.constants.skill_level_constants import SkillLevelConstants
from operator import itemgetter

def compute_preferences(project: Project, user: User):
    project_specs = project.get_specializations()
    user_specs = user.get_specializations()
    pref = 5

    for spec, level in user_specs.items():
        if spec in project_specs:
            skill_modifier = SkillLevelConstants.get_skill_level_value(level)
            pref += skill_modifier

    in_projects = len(user.get_projects_joined()) + 2 * len(user.get_projects_owned())
    pref -= in_projects

    return pref

def order_preference_dictionary(pref_dict):
    for key, value in pref_dict.items():
        pref_dict[key] = sorted(value, key=itemgetter(1), reverse=True)


def matching_round(matching):
    decision = {}
    for key, value in matching.items():
        for user in value:
            if user[0] not in [x[0] for x in decision.values()]:
                if key not in decision.keys():
                    decision[key] = user
                elif user[1] > decision[key][1]:
                    decision[key] = user

    for key, value in decision.items():
        Project.get(key).accept_user_application(User.get(value[0]))

def perform_match():
    """{project : [[user, pref], [user, pref], ...], ...}"""
    conns = project_connectors.query.filter_by(relation="Applicant").all()
    matching = {}
    for conn in conns:
        project = Project.get(conn.project_id)
        user = User.get(conn.user_id)
        compute_preferences(project, user)

        if project.id not in matching.keys():
            matching[project.id] = []

        pref = compute_preferences(project, user)
        matching[project.id].append([user.id, pref])
    order_preference_dictionary(matching)
    matching_round(matching)
    if matching != {}:
        perform_match()
    print("Done")
