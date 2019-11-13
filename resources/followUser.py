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


class FollowUser(Resource):

    @requires_auth
    def post(self, user_id):
        if not g.current_user.get('user_id',  None):
            return Response('Not authorized', 401)
        oid = bson.objectid.ObjectId(g.current_user.get('user_id'))
        try:
            query = {
                '_id': bson.objectid.ObjectId(user_id)
            }
            UserModel.objects(__raw__=query).update_one(upsert=False, add_to_set__followers=oid)
            return 'followed user'
        except:
            return Response("could not follow user", 400)

    @requires_auth
    def delete(self, user_id):
        if not g.current_user.get('user_id',  None):
            return Response('Not authorized', 401)
        oid = bson.objectid.ObjectId(g.current_user.get('user_id'))
        try:
            query = {
                '_id': bson.objectid.ObjectId(user_id)
            }
            UserModel.objects(__raw__=query).update_one(upsert=False, pull__followers=oid)
            return 'unfollowed user'
        except Exception as e:
            print(e)
            return Response("could not unfollow user", 400)

