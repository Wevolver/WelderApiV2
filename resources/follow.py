from auth.decorators import requires_permission_to
from flask import current_app as app
from flask_restful import Resource
from resources.models import *
from flask import Response
from flask import jsonify
from flask import request
from flask import abort
import logging
import json
import bson
from auth.auth0 import requires_auth
from flask import g

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class FollowTag(Resource):

    @requires_auth
    def post(self):
        error_message = json.dumps(
            {'Message': 'Tag could not be followed'})

        params = request.json

        if not g.current_user:
            return Response(error_message, 401)

        oid = None
        try:
           oid = bson.objectid.ObjectId(g.current_user.get('user_id'))
        except:
            pass
        try:
            query = {'_id': oid }
            user = UserModel.objects.get(__raw__=query)
        except UserModel.DoesNotExist as e:
            # user = UserModel(legacy_id = auth_user['id'])
            return Response(error_message, 401)

        # user.email = params.get('email', None)
        tagId = params.get('tagId', None)
        if tagId:
            if tagId not in user.tags_followed:
                tagSet = set(user.tags_followed)
                tagSet.add(params['tagId'])
                user.tags_followed = list(tagSet)
                query = {
                    'name': params.get('tagId')
                }
                TagModel.objects(__raw__=query).update_one(upsert=False, inc__followCount=1)

        user.save()

        query = {
            'name': {'$in': user['tags_followed']}
        }
        tags = TagModel.objects(__raw__=query)
        user['tags_followed'] = json.loads(tags.to_json())
        return json.loads(user.to_json())

    @requires_auth
    def delete(self):
        # User follows a specific tag...
        # needs user email and legacy id
        error_message = json.dumps(
            {'Message': 'Tag could not be unfollowed'})

        params = request.json
        if not g.current_user:
            return Response(error_message, 401)

        oid = None
        try:
           oid = bson.objectid.ObjectId(g.current_user.get('user_id'))
        except:
            pass
        try:
            query = {'_id': oid }
            user = UserModel.objects.get(__raw__=query)
            if params.get('tagId', None) and params.get('tagId') in user.tags_followed:
                user.tags_followed.remove(params['tagId'])
            else:
                query = {
                    'name': {'$in': user['tags_followed']}
                }
                tags = TagModel.objects(__raw__=query)
                user['tags_followed'] = json.loads(tags.to_json())
                response = json.loads(user.to_json())
                return Response(response)
            user.save()
            query = {
                'name': params.get('tagId')
            }
            TagModel.objects(__raw__=query).update_one(upsert=False, inc__followCount=-1)
            # tag = TagModel.objects.get(__raw__=query)
            # tag.followCount = (tag.followCount - 1) if (tag.followCount - 1) > 0 else 0
            # tag.save()
            tag_objects = []
            # for tag in user['tags_followed']:
            query = {
                'name': {'$in': user['tags_followed']}
            }
            tags = TagModel.objects(__raw__=query)
                # if tag:
                #     tag_objects.append(json.loads(tag[0].to_json()))
            user['tags_followed'] = json.loads(tags.to_json())
            response = json.loads(user.to_json())
        except UserModel.DoesNotExist as e:
            response = error_message
        return response
