from auth.decorators import requires_permission_to
from flask import current_app as app
from flask_restful import Resource
from resources.models import *
from flask import Response
from flask import jsonify
from flask import request
from bson.json_util import dumps
from flask import abort
from flask import g
import logging
import json
import bson
from auth.auth0 import requires_auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Bookmarks(Resource):

    @requires_auth
    def get(self, user_id):
        # if not auth_user or auth_user['id'] != user_id:
        #     return {'message': 'Not authorized'}, 401
        try:
            limit = int(request.args.get('limit', 0))
            try:
                query =  { '$or': [
                    {'legacy_user_id': int(user_id)},
                    { 'user_id':  bson.objectid.ObjectId(request.args.get('oid'))},
                ]}
            except:
                query = {'legacy_user_id': 0}
                pass
            pipeline =  [
                { "$match": query },
                { "$sort": {"_id": -1}},
                { "$skip": 0 },
                { "$limit": limit },
                { '$lookup':
                    {
                        'from': 'project',
                        'localField': "project_id",
                        'foreignField': "_id",
                        'as': "project"
                    }
                },
                {"$unwind": "$project"},
            ]
            bookmarks = list(BookmarkModel.objects.aggregate(*pipeline))
            project_ids = []
            for bookmark in bookmarks:
                project_ids.append(bookmark['project']['_id'])

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

            for bookmark in bookmarks:
                project = bookmark['project']
                for bookmark_count in bookmark_counts:
                    project['bookmark_count'] = project.get('bookmark_count', 0)
                    if str(bookmark_count['_id']) == str(project['_id']):
                        if g.current_user.get('user_id'):
                            user_ids = bookmark_count.get('user_ids', [])
                            project['bookmarked'] =  bson.objectid.ObjectId(g.current_user.get('user_id')) in user_ids
                        project['bookmark_count'] = project['bookmark_count'] + len(bookmark_count['user_ids'])


            return json.loads(dumps(bookmarks))
        except Exception as e:
            print(e)
            response = "Bad Request"
        return response

    @requires_auth
    def delete(self, user_id):
        if not g.current_user:
            return Response("Not authorized", 401)
        try:
            user_id = bson.objectid.ObjectId(g.current_user.get('user_id'))
        except:
            user_id = None
            pass
        try:
            query = {
                '$or':[{'legacy_user_id': user_id}, {'user_id': user_id}],
                'project_id': bson.objectid.ObjectId(request.json.get('project_id'))
            }
            bookmark = BookmarkModel.objects(__raw__=query)
            bookmark.delete()
            return Response("Deleted bookmark", 200)
        except Exception as e:
            print(e)
            return Response("Couldnt delete this bookmark", 401)

    @requires_auth
    def post(self, user_id):
        error_message = json.dumps(
            {'Message': 'Bookmark could not be created for this project'})

        if not g.current_user:
            return Response(error_message, 401)
        try:
            project_id = request.json.get('project_id')
            if not project_id:
                return Response(error_message, 401)
            bookmark = {}

            if user_id:
                bookmark['legacy_user_id'] =  user_id

            if request.args.get('oid'):
                try:
                    bookmark['user_id'] =  bson.objectid.ObjectId(request.args.get('oid'))
                except:
                    pass

            bookmark['project_id'] = bson.objectid.ObjectId(project_id)
            user_bookmark = BookmarkModel.objects(__raw__=bookmark).modify(upsert=True, new=True, set__project_id=project_id)
            # Location.objects(user_id=user_id).update_one(set__point=point, upsert=True)
            project = ProjectModel.objects.with_id(str(project_id))

            if int(project['privacy']) != 2 and g.current_user and project:
                user_bookmark.save()
                return json.loads(user_bookmark.to_json())
            # elif project['privacy'] == 2 and g.current_user and project:
                # auth_user_id = auth_user['id']
                # if any(member.get('id', None) == auth_user_id for member in project['members']):
                #     user_bookmark.save()
                #     return json.loads(user_bookmark.to_json())
                # else:
                #     return Response(error_message, 400)
            else:
                return Response(error_message, 400)
        except:
            return Response(error_message, 400)
