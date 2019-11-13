from resources.projects import generate_project_slug
from datetime import datetime, timedelta
from auth.auth0 import requires_auth
from flask_restful import Resource
from resources.models import *
from flask import Response
from flask import request
from flask import g
import logging
import bson
import json
import jwt

logger = logging.getLogger()


class Permissions(Resource):


    def encode(self, permissions, user, project, minutes):
        encoded = ''
        with open('auth/jwt.sign','r') as sign:
            encoded = jwt.encode({'exp': datetime.utcnow() + timedelta(seconds=minutes*60),
                                  'iss': 'wevolver',
                                  'user': user,
                                  'project': project,
                                  'permissions': '{}'.format(permissions)}, sign.read(), algorithm='RS256')
        return encoded

    @requires_auth
    def post(self):
        """
        Grabs the project from the database and updates it with whatever values
        are sent in the request.
        """

        auth_user = None
        is_member = False
        members = {'$in':[]}
        user_id = request.json.get('user_id', 1)
        permission_list = {
            'private': {'member': ['read', 'write', 'create'], 'guest': ['none', 'create']},
            'public': {'member': ['read', 'write', 'create'], 'guest': ['read', 'create']},
        }

        try:
            user_slug, project_name = request.json['project'].split('/')
        except:
            user_slug, project_name = (None, '')

        if g.current_user.get('sub'):
            query = {
                'auth0_id': g.current_user.get('sub'),
            }
            try:
                auth_user = UserModel.objects.get(__raw__=query)
            except:
                print('No user with that auth0 id')

        if auth_user:
            members['$in'] += [auth_user.legacy_id, auth_user.id]

        if user_id:
            members['$in'] += [int(float(user_id))]

        query = {
            'user_slug': user_slug,
            'slug': generate_project_slug(project_name),
            'members': {'$elemMatch': {
                'id': members
            }},
        }
        
        try:
            project = ProjectModel.objects.get(__raw__=query)
            is_member = True
        except:
            query = {
                'user_slug': user_slug,
                'slug': generate_project_slug(project_name),
                'privacy': 0,
            }
            try:
                project = ProjectModel.objects.get(__raw__=query)
            except:
                project = None
                pass
            pass

        if (auth_user or (user_id and user_id != 1)) and is_member:
            membership = 'member'
        else:
            membership = 'guest'

        if project:
            privacy = 'private' if project.privacy is not 0 else 'public'
            name = project.name
        else:
            privacy = 'public'
            name = 'default'

        permission_claims = permission_list[privacy][membership]
        user = str(auth_user.id) if auth_user else 'default'
        token = self.encode(permission_claims, user, name, 1)
        response = token.decode("utf-8")
        return Response(response, mimetype='text/html')
