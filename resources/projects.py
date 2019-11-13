from auth.decorators import requires_permission_to
from boto3.dynamodb.conditions import Attr
from flask import current_app as app
from flask_restful import Resource
from bson.json_util import dumps
from resources.models import *
from datetime import datetime
from decimal import Decimal
from flask import Response
from flask import request
from flask import jsonify
from flask import abort
from flask import g
import requests
import logging
import uuid
import json
import re
import bson
from auth.auth0 import requires_auth


logger = logging.getLogger()
logger.setLevel(logging.INFO)

MEMBER_ROLE = 0
ADMIN_ROLE = 1

class Projects(Resource):
    with open('resources/plans.json') as data_file:
        plans = json.loads(data_file.read())

    @requires_auth
    def get(self):
        '''
            Reads the full list of v2 projects
        '''

        try:
            _arg_legacy_id = request.args.get('legacy_id')
            _arg_oid = g.current_user.get('user_id')

            oid = None
            legacy_id = None
            try:
                legacy_id = int(_arg_legacy_id)
            except:
                pass

            try:
                oid = bson.objectid.ObjectId(_arg_oid)
            except:
                pass

            if not legacy_id and not oid:
                abort(400)


            privacy = 0
            skip = int(request.args.get('skip', 0))
            limit = int(request.args.get('limit', 2))
            if g.current_user and g.current_user['user_id'] == request.args.get('oid'):
                privacy = {'$in': [0, 2]}
            pipeline = [
                {'$match': {
                    'privacy': privacy,
                    'members': {'$elemMatch':
                        {'id': {'$in':[legacy_id, bson.objectid.ObjectId(request.args.get('oid'))]}},
                    }
                }},
                {'$sort': {'_id': -1}},
                {
                  "$facet": {
                    "projects": [
                      { "$skip": skip },
                      { "$limit": limit },
                    ],
                    "totalCount": [
                        {
                            "$count": 'count'
                        }
                    ]
                  },
                },
                { "$project" :
                    {
                        "totalCount" : { "$arrayElemAt": [ "$totalCount.count", 0 ] },
                        "projects": 1,
                    },
                }
            ]

            projects = list(ProjectModel.objects.aggregate(*pipeline))
            response = json.loads(dumps(projects[0]))

            project_ids = []
            for project in projects[0]['projects']:
                project_ids.append(project['_id'])

            pipeline = [
                {
                    '$match': {
                        'project_id': {'$in': project_ids}
                    }
                },
                {
                    '$group' : {
                        '_id' : "$project_id",
                        'user_ids': { '$push': "$legacy_user_id" },
                    }
                }
            ]

            bookmark_counts = list(BookmarkModel.objects.aggregate(*pipeline))
            for project in response['projects']:
                for bookmark_count in bookmark_counts:
                    project['bookmark_count'] = project.get('bookmark_count', 0)
                    if str(bookmark_count['_id']) == project['_id']["$oid"]:
                        if oid or legacy_id:
                            user_ids = bookmark_count.get('user_ids', [])
                            project['bookmarked'] = legacy_id in user_ids or oid in user_ids

                        project['bookmark_count'] = project['bookmark_count'] + len(bookmark_count['user_ids'])

        except Exception as e:
            response = "Bad Request"
            print(e)
        return response

    @requires_auth
    def post(self):

        user = request.json.get('user')
        project = request.json.get('project')

        if not project or not user:
            abort(400)

        if not g.current_user or not user['slug']:
            return {'message': 'Not authorized'}, 401

        auth_user = UserModel.objects.get(auth0_id=g.current_user['sub'])

        try:
            project['created_user_id'] = auth_user.id
            project['members'] = [{'id': project['created_user_id'], 'permission': ADMIN_ROLE }]
            project['followers'] = []
            project['privacy'] = int(float(project['privacy']))
            project['license'] = project.get('license' , '')
            project_name = project.get('name').strip()
            project['name'] = project_name
            project['welder_uri'] = '{}/{}/{}'.format(
                app.config.get('WELDER_BASE_URL'),
                user.get('slug'),
                project_name)
            project['user_slug'] = user.get('slug', None)

            if(project.get('version3', False)):
              project['version'] = '3'
            else:
              project['version'] = '2'

            project['university'] = project.get('university', "")
            project.pop('version3', None)

            project['slug'] = generate_project_slug(project_name)
            project['created_at'] = datetime.utcnow()
            project['picture'] = project.get('picture')
            project_s = ProjectModel(**project)
            user_projects_count = ProjectModel.objects(
                created_user_id= auth_user.id
            ).count()

            if not auth_user.plan:
                auth_user.plan = 'free'
            user_can_create = can_user_create_project(
                Projects.plans[auth_user.plan], user_projects_count,
                project.get('privacy'))

            if not user_can_create:
                error_message = json.dumps({'Message': 'You have exceeded the maximum number of projects allowed per account. Please contact us at info@welder.app.'})
                return Response(error_message, 401)

            data = {
                'user_id': auth_user.id,
                'is_welder': 'true',
                'cloning_user': project.get('user_slug'),
            }
            headers = {
                'Authorization':
                '{}'.format(request.headers.get('Authorization', ''))
            }

            welder_url = '{}/create?privacy={}&action=create'.format(
                project.get('welder_uri'), project.get('privacy'))

            welder_response = requests.post(
                welder_url, data=data, headers=headers)
            welder_response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            error_message = json.dumps({'Message': e.response.content.decode("utf-8")})
            abort(Response(error_message, 401))
        except requests.exceptions.RequestException as e:
            print(e)
            error_message = json.dumps({'Message': 'Creation Failed'})
            abort(Response(error_message, 401))
        except Exception as e:
            print(e)
            error_message = json.dumps({'Message': 'Creation Failed'})
            abort(Response(error_message, 401))
        else:
            project_s.save()
            return json.loads(project_s.to_json())
        error_message = json.dumps({'Message': 'Project could not be created'})
        return Response(error_message, 401)


def can_user_create_project(plan, number_of_projects, privacy):
    can_create = True
    if not plan['privateAllowed'] and privacy is not 0:
        can_create = False
    if number_of_projects >= plan['numberOfProjects']:
        can_create = False
    return can_create

def generate_project_slug(s):
    slug = re.sub('[^0-9a-zA-Z-_]+', '.', s)
    return slug.lower()
