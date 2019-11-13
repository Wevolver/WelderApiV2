from flask import current_app as app
from auth.decorators import requires_permission_to
from flask_restful import Resource
from resources.models import *
from datetime import datetime
from flask import Response
from flask import request
import requests
import json
import bson
from bson.json_util import dumps

class UsersComments(Resource):
    def get(self, user_id):
        try:
            skip = int(request.args.get('skip', 0)) * 5

            try:
                query = { 'author': int(user_id) }
            except:
                query = { 'author_id':  bson.objectid.ObjectId(request.args.get('oid'))}
                pass
            pipeline =  [
                { "$match": query},
                { "$sort": {"_id": -1}},
                { "$skip": skip },
                { "$limit": 5 },
                { '$lookup':
                    {
                        'from': 'project',
                        'localField': "discusses",
                        'foreignField': "_id",
                        'as': "project",
                    }
                },
                { "$redact": {
                    "$cond": {
                       "if":
                          { "$ne": [ "$privacy", 2 ] } ,
                          "then": "$$DESCEND",
                          "else": "$$PRUNE"
                    }
                }},
                {"$unwind": "$project"},
                { "$project": {
                    "project_slug": "$project.slug",
                    "project_name": "$project.name",
                    "project_user_slug": "$project.user_slug",
                    "project_picture":"$project.picture",
                    "text": 1,
                    "author": 1,
                    "privacy": 1,
                    "dateCreated": 1,
                    "parentItem": 1,
                }}
            ]
            comments = list(CommentModel.objects.aggregate(*pipeline))
            return json.loads(dumps(comments))
        except Exception as e:
            print(e)
            error_message = json.dumps({'Message': 'Nothing to see here.'})
            return Response(error_message, 401)
