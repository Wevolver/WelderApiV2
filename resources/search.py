from auth.decorators import requires_permission_to
from flask_restful import Resource
from flask import request
from flask import g
import logging
import json
from resources.models import *
import bson
from bson.json_util import dumps
from auth.auth0 import requires_auth

logger = logging.getLogger()

class Search(Resource):
    @requires_auth
    def get(self):
        """
        Grabs the project from the database and updates it with whatever values
        are sent in the request.
        """
        oid = None
        legacy_id = None
        try:
            legacy_id = int(_arg_legacy_id)
        except:
            pass

        try:
            oid = bson.objectid.ObjectId(g.current_user.get('user_id'))
        except:
            pass
        try:
            tags = request.args.get('tags', '')
            hidden_tags = request.args.get('hiddenTags', '')
            if not tags and not hidden_tags:
                hidden_tags = 'featured'
            print(hidden_tags)
            limit = int(request.args.get('limit', 9))
            nextId = request.args.get('next', None)

            if not tags and not hidden_tags:
                return []

            query = {
                'privacy': 0,
                'picture.source': {'$exists': True},
                'description': {'$exists': True, '$ne': ''},
            }

            if tags:
                if 'careables' in tags:
                    query['tags'] = {'$all': tags.split(',')}
                else:
                    query['tags'] = {'$in': tags.split(',')}

            if hidden_tags and not 'careables' in tags:
                query['hidden_tags'] = {'$in': hidden_tags.split(',')}

            if nextId:
                query['_id'] =  {'$lt': bson.objectid.ObjectId(nextId)}

            pipeline = [
                {
                    '$match': query
                },
                { '$sort' : { '_id': -1 } },
                { '$limit' : limit },
                {
                '$lookup':
                     {
                        'from': 'tag',
                        'localField': "tags",
                        'foreignField': "name",
                        'as': "tags"
                    }
                }
            ]

            projects = list(ProjectModel.objects.aggregate(*pipeline))
            response = projects
            project_ids = []
            for project in projects:
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
                        'user_ids': { '$push': {"legacy_user_id":"$legacy_user_id", "user_id": "$user_id"} },
                    }
                }
            ]

            bookmark_counts = list(BookmarkModel.objects.aggregate(*pipeline))

            for project in response:
                for bookmark_count in bookmark_counts:
                    project['bookmark_count'] = project.get('bookmark_count', 0)
                    if bookmark_count['_id'] == project['_id']:
                        if oid or legacy_id:
                            user_ids = bookmark_count.get('user_ids', [])
                            for user_id in user_ids:
                                project['bookmarked'] =  user_id.get('user_id') == oid or user_id.get('legacy_user_id') == legacy_id
                        project['bookmark_count'] = project['bookmark_count'] + len(bookmark_count['user_ids'])

        except Exception as inst:
            response = "Couldn't search"
            logger.info((inst))
        return json.loads(dumps(response))
