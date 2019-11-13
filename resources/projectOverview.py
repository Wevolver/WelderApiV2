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

class ProjectOverview(Resource):

    @requires_auth
    def post(self, project_id):
        auth_user = None
        if not g.current_user.get('sub', None):
            return {'message': 'Not authorized'}, 401
        else:
            auth_user = UserModel.objects.get(id=bson.objectid.ObjectId(g.current_user.get('user_id')))
            auth_user = {'id': auth_user.legacy_id, 'oid': auth_user.id, 'plan':'free'}
        try:
            project_updates = request.json
            p_id = bson.objectid.ObjectId(project_id)
            query = {
                '_id': p_id,
                'members': {'$elemMatch': {'id': {'$in':[auth_user['id'], auth_user['oid'], str(auth_user['oid'])]}}},
            }

            project = ProjectModel.objects.get(__raw__=query)

            if request.json.get('spec_table', False):
                for obj in request.json['spec_table']:
                    for k in list(obj.keys()):
                      if k == '_id':
                        del obj[k]

            if request.json.get('sources', False):
                for obj in request.json['sources']:
                    for k in list(obj.keys()):
                      if k == '_id':
                        del obj[k]

            if request.json.get('gallery', False):
                for obj in request.json['gallery']:
                    for k in list(obj.keys()):
                      if k == '_id':
                        del obj[k]

            project.overview = OverviewModel(**request.json)
            project.save()
            response = json.loads(project.to_json())
        except Exception as inst:
            logger.info((inst))
            print(inst)
            return {"message": "Couldn't update this project"}, 400
        return response
