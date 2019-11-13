from auth.decorators import requires_permission_to
from boto3.dynamodb.conditions import Attr
from flask import current_app as app
from flask_restful import Resource
from bson.json_util import dumps
from resources.models import *
from decimal import Decimal
from flask import jsonify
from flask import request
from flask import abort
from flask import g
from datetime import datetime
import requests
import logging
import json
import re
from utils.emailSES import sendInviteMemberEmail
from bson.json_util import dumps
import bson
from auth.auth0 import requires_auth

logger = logging.getLogger()

# Constants
MEMBER_ROLE = 0
ADMIN_ROLE = 1

class Project(Resource):
    with open("resources/plans.json") as data_file:
        plans = json.loads(data_file.read())

    @requires_auth
    def get(self, user_slug, project_slug):
        """
        Reads a single project by the given id.
        """

        auth_user_id = g.current_user.get('user_id', None)
        try:
            query = {'user_slug': user_slug, 'slug': project_slug}
            pipeline = [
                {
                    '$match': query
                },
                { '$limit' : 1 },
                {'$lookup':
                     {
                        'from': 'tag',
                        'localField': "tags",
                        'foreignField': "name",
                        'as': "tags"
                    }
                },
                {'$lookup':
                     {
                        'from': 'bookmark_model',
                        'localField': "_id",
                        'foreignField': "project_id",
                        'as': "bookmarks"
                    }
                }
            ]
            project = list(ProjectModel.objects.aggregate(*pipeline))[0]
            project['bookmark_count'] = project.get('bookmark_count',0) + len(project.get('bookmarks', []))
            response = None
            if not project:
                abort(401, "Couldn't find this project")

            if not g.current_user.get('sub', None) and project['privacy'] == 2:
                abort(401, "Can't view this project")

            if g.current_user.get('sub', None) and project['privacy'] == 2:
                auth_user = UserModel.objects.get(id=bson.objectid.ObjectId(g.current_user.get('user_id')))
                if not auth_user:
                    abort(401, "Couldn't find this project")
                for member in project['members']:
                    member_id = member.get('id', None)
                    try:
                        int_member_id = int(member_id)
                    except:
                        int_member_id = 0
                    print(str(member_id))
                    print(auth_user_id)
                    print(auth_user.legacy_id)
                    if str(member_id) == str(auth_user_id) or str(int_member_id).split(".")[0] == str(auth_user.legacy_id):
                        response = project

            if project['privacy'] == 0:
                response = project

            if auth_user_id:
                for bookmark in project['bookmarks']:
                    try:
                        response['bookmarked'] = bookmark.get('user_id') == bson.objectid.ObjectId(auth_user_id)
                    except:
                        pass
            if not response:
                abort(401, "Couldn't find this project")
            response.pop('bookmarks', None)
            response['api_version'] = 2
        except Exception as e:
            print(e)
            logger.info(e)
            abort(400, "Something went wrong")
        return json.loads(dumps(response))

    @requires_auth
    def put(self, user_slug, project_slug):
        """
        Grabs the project from the database and updates it with whatever values
        are sent in the request.
        """
        auth_user = None
        if not g.current_user.get('sub', None):
            return {'message': 'Not authorized'}, 401
        else:
            auth_user = UserModel.objects.get(id=bson.objectid.ObjectId(g.current_user.get('user_id')))
            if not auth_user.plan:
                auth_user = {'id': auth_user.legacy_id, 'oid': auth_user.id, 'plan': 'free'}
            else:
                auth_user = {'id': auth_user.legacy_id, 'oid': auth_user.id, 'plan': auth_user.plan}

        try:
            project_updates = request.json
            query = {
                'user_slug': user_slug,
                'slug': project_slug,
                'members': {'$elemMatch': {'id': {'$in':[auth_user['id'], auth_user['oid']]}, 'permission': ADMIN_ROLE}},
            }

            try:
                project = ProjectModel.objects.get(__raw__=query)
            except Exception as e:
                if project_updates.get("follower", None) and project_updates.get("follower") == auth_user.id:
                    query = {
                        'user_slug': user_slug,
                        'slug': project_slug,
                    }
                    project = ProjectModel.objects.get(__raw__=query)
                    followers = project.followers
                    followers.append({'legacy_id': project_updates.get("follower"), 'created_at': datetime.utcnow()})
                    project.followers = followers
                    project.save()
                    return json.loads(project.to_json()), 200
                else:
                    return {'message': 'Not authorized. Only an admin can perform this action.'}, 401

            if project_updates.get('members', None):
                members = {str(member.get('id')): member for member in project.members}

                for member_details in project_updates.get('members', []):
                    mid = member_details.get('id')
                    try:
                        oid = mid.get('$oid', None)
                        mid = bson.objectid.ObjectId(oid)
                    except:
                        mid = bson.objectid.ObjectId(member_details.get('id'))
                        member_details['id'] = mid

                    if members.get(str(mid)):
                        members.get(str(mid))['permission'] = member_details['permission']

                    if member_details.get('deleted', False):
                        adjustedMembers = {}
                        for member in members.keys():
                            if(members[member]['id'] != mid):
                                adjustedMembers[member] = members[member]
                        members =  adjustedMembers
                    elif str(mid) != auth_user['id'] and not members.get(str(mid)):
                        if(member_details.get('email', None)):
                            sendInviteMemberEmail(member_details.get('email'), project_updates.get('name', project.name), project.user_slug, project.slug)
                        member_details.pop('email', None)
                        members[str(mid)] = member_details

                admin_exists = False
                for member in members:
                    if members[member].get('permission') == ADMIN_ROLE:
                        admin_exists = True
                if not admin_exists:
                     return {'message': 'There must be at least one admin per project.'}, 400
                project.members = [{'id': members[member]['id'], 'permission': members[member]['permission']} for member in members]
            else:
                user_plan = "free" if not auth_user['plan'] else auth_user['plan']
                if user_plan == 'free' and project["privacy"] == 0 and project_updates['privacy']:
                    abort(400)
                project.privacy =  project_updates['privacy']
                if(project_updates.get('license', None)):
                    project.license =  project_updates.get('license')['value']
                project.picture =  project_updates.get('picture', None)
                if project_updates.get('university', None):
                    project.university = project_updates.get('university', None)
                if project_updates.get("description", None):
                    project.description = project_updates.get('description')
                if(project_updates.get('version3', False)):
                  project['version'] = '3'
                else:
                  project['version'] = '2'
                project_updates.pop('version3', None)

                if 'hiddenTags' in project_updates:
                    project['hidden_tags'] = project_updates.get('hiddenTags', [])
                url = "{}/{}/{}/rename".format(
                    app.config.get('WELDER_BASE_URL'), project.user_slug,
                    project['name'])

                if project_updates.get("name", None) and project_updates.get("name") != project['name']:
                    data = {'new_name': project_updates["name"], 'is_welder': True}
                    authorization = request.headers.get('Authorization', '')
                    params = {'user_id': auth_user.get('id')}
                    headers = {
                        'AUTHORIZATION': '{}'.format(authorization, '')
                    }
                    try:
                        response = requests.post(url, params=params, data=data, headers=headers)
                        response.raise_for_status()
                    except requests.exceptions.HTTPError:
                        abort(401)
                    except requests.exceptions.RequestException:
                        abort(400)
                    else:
                        project.name = project_updates.get('name')
                        project.slug = generate_project_slug(project_updates.get('name'))
            project.save()


            query = {
                'user_slug': user_slug,
                'slug': project_slug,
                'members': {'$elemMatch': {'id': {'$in':[auth_user['id'], auth_user['oid']]}, 'permission': ADMIN_ROLE}},
            }
            pipeline = [
                {
                    '$match': query
                },
                { '$limit' : 1 },
                {'$lookup':
                     {
                        'from': 'tag',
                        'localField': "tags",
                        'foreignField': "name",
                        'as': "tags"
                    }
                }
            ]
            project = list(ProjectModel.objects.aggregate(*pipeline))[0]
            response = json.loads(dumps(project))
        except Exception as inst:
            print(inst)
            return {"message": "Couldn't update this project"}, 400
        return response

    @requires_auth
    def delete(self, user_slug, project_slug):
        """
        Deletes the project from the api, and removes its repository from Welder.
        If the project was a fork or has been forked then the forks are updated.
        """
        if not g.current_user.get('user_id', None):
            return {'message': 'Not authorized'}, 401
        auth_user = UserModel.objects.get(auth0_id=g.current_user['sub'])
        oid = None
        try:
            oid = bson.objectid.ObjectId(g.current_user.get('user_id', None))
        except:
            pass

        try:
            query = {
                'user_slug': user_slug,
                'slug': project_slug,
                'members': {
                    '$elemMatch': {
                        'id': {'$in': [auth_user.id, oid, g.current_user.get('user_id', "")]},
                        'permission': ADMIN_ROLE
                    }
                },
            }
            project = ProjectModel.objects.get(__raw__=query)
            user = request.json['user']
            if not project or not user:
                return {'message': 'Not authorized'}, 401
            delete_url = "{}/{}/{}/delete".format(
                app.config.get('WELDER_BASE_URL'), user.get('slug'),
                project.name)
            params = {'user_id': user.get('id')}
            data = {'is_welder': True}
            headers = {
                'AUTHORIZATION':
                '{}'.format(request.headers.get('AUTHORIZATION', ''))
            }
            try:
                response = requests.post(
                delete_url, data=data, params=params, headers=headers)
                response.raise_for_status()
                project.delete()
            except Exception as e:
                print(e)
                return "Couldn't delete this project's repository", 400
        except Exception as inst:
            response = "Couldn't delete this project"
            print(inst)
            logger.info((inst))
        response = "Deleted project"
        return response

def generate_project_slug(s):
    slug = re.sub('[^0-9a-zA-Z-_]+', '.', s)
    return slug.lower()
