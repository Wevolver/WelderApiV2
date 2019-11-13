from resources.projects import generate_project_slug
from resources.projectImage import ProjectImage
from resources.permissions import Permissions
from resources.bookmarks import Bookmarks
from resources.userImage import UserImage
from resources.activity import Activity
from resources.projects import Projects
from resources.project import Project
from resources.comment import Comment
from resources.usersComments import UsersComments
from resources.relatedProjects import RelatedProjects
from resources.search import Search
from resources.searchQuery import SearchQuery
from resources.tags import Tags
from resources.tagCategories import TagCategories
from resources.projectOverview import ProjectOverview
from resources.users import Users
from resources.fork import Fork
from resources.user import User
from resources.follow import FollowTag
from resources.followUser import FollowUser
from resources.usersSearch import UsersSearch
from resources.models import *

from mongoengine import connect
from flask_restful import Api
from flask_cors import CORS
from flask import Flask
import click
import json
import os

app = Flask(__name__)

CORS(app)
app.config.from_object('settings.DevelopmentConfig')
api = Api(app)
api_prefix = '/api/v2'
api.add_resource(Projects, api_prefix + '/projects')
api.add_resource(Users, api_prefix + '/users')
api.add_resource(User, api_prefix + '/users/<slug_or_id>')
api.add_resource(FollowUser, api_prefix + '/users/<user_id>/follow')
api.add_resource(Bookmarks, api_prefix + '/bookmarks/<int:user_id>')
api.add_resource(ProjectImage, api_prefix + '/project/image')
api.add_resource(UserImage, api_prefix + '/user/image')
api.add_resource(UsersComments, api_prefix + '/user/comments/<user_id>')
api.add_resource(ProjectOverview, api_prefix + '/project/<project_id>/overview')
api.add_resource(Comment, api_prefix + '/comments/<discusses_id>')
api.add_resource(Project, api_prefix + '/project/<user_slug>/<project_slug>')
api.add_resource(Fork, api_prefix + '/projects/forks/<int:id>')
api.add_resource(RelatedProjects, api_prefix + '/projects/related')
api.add_resource(Search, api_prefix + '/search')
api.add_resource(UsersSearch, api_prefix + '/search/users')
api.add_resource(SearchQuery, api_prefix + '/query')
api.add_resource(Activity, api_prefix + '/activity')
api.add_resource(Permissions, api_prefix + '/permissions')
api.add_resource(Tags, api_prefix + '/tags')
api.add_resource(TagCategories, api_prefix + '/tags/categories')
api.add_resource(FollowTag, api_prefix + '/tags/follow')

connect(host=app.config.get("DATABASE_HOST", "wevolver"))

@app.cli.command()
def change_forkorigins_to_reference():
    """Initialize the database."""
    query =  {'fork_origin': { '$exists': True }}
    projects = ProjectModel.objects(__raw__=query)
    for project in projects:
        click.echo(project.fork_origin)
    click.echo('Projects: ' + str(projects.count()))

@app.cli.command()
def import_project_from_json_file():
    click.echo('Importing projects from data.json')
    with open('../dumps/dump_prod.json', 'r') as file:
        dump = file.read()
        dump = json.loads(dump)
        projects = dump['projects']
        conuter = 0
        for project in projects:
            if not project['user_slug']:
                continue
            try:
                new_project = ProjectModel(**project)
                new_project.imported = True
                new_project.slug = generate_project_slug(new_project.name)
                new_project.save()
                conuter = conuter + 1
            except Exception as e:
                print(e)
                continue
        click.echo('Projects saved: ' + str(conuter))
