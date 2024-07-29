from data.classes import User
from data.Routing import *
from data.matching import perform_match

@app.route('/')
def display_landing_page(content=None):
    current_user = User.set_connected_user_by_current_cookie()
    projects = []
    if current_user is not None:
        projects = current_user.get_projects_owned()
    return render_template('landing_page.html', current_user=current_user, projects=projects)

if __name__ == "__main__":
    app.run()
