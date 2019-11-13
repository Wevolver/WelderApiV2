from auth.decorators import requires_permission_to
from flask_restful import Resource
from bson.json_util import dumps
from resources.models import *
from flask import Response
from flask import request
from flask import abort
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class RelatedProjects(Resource):
    def get(self):
        try:
            tags = request.args.get('tags', '').split(',')
            name = request.args.get('name', '')
            pipeline = [
              { "$match": {
                   "tags": { "$in": tags },
                   "name": { "$ne": name},
                   'privacy': 0,
                   'picture.source': {'$exists': True},
                   'description': {'$exists': True, '$ne': ''},
                   'hidden_tags': 'featured',
                }
              },
              { "$project": {
                "ID": 1,
                "tags": 1,
                "name": 1,
                "slug": 1,
                "description": 1,
                "created_at": 1,
                "picture": 1,
                "welder_uri" : 1,
                "created_user" : 1,
                "user_slug" : 1,
                "privacy" : 1,
                "imported" : 1,
                "forkers" : 1,
                "members" : 1,
                "legacy_id" : 1,
                "bookmark_count" : 1,
                "order": {
                  "$size": {
                    "$setIntersection": [ tags, "$tags" ]
                  }
                }
              }},
              { "$sort": { "order": -1 } },
              { '$limit' : 3 },

                            { "$lookup": {
                     "from": "tag",
                     "localField": "tags",
                     "foreignField": "name",
                     "as": "tagObjects"
                  }
              },
              { "$group": {
                      "_id": "$_id",
                      "name": { '$first': "$name"},
                      "tags": { "$first": "$tagObjects" },
                      "slug": { "$first": "$slug" },
                      "description": { "$first": "$description" },
                      "created_at": { "$first": "$created_at" },
                      "picture": { "$first": "$picture" },
                      "welder_uri" : { "$first": "$welder_uri" },
                      "created_user" : { "$first": "$created_user" },
                      "user_slug" :{ "$first": "$user_slug" },
                      "privacy" : { "$first": "$privacy" },
                      "imported" : { "$first": "$imported" },
                      "forkers" : { "$first": "$forkers" },
                      "members" : { "$first": "$members" },
                      "legacy_id" : { "$first": "$legacy_id" },
                      "bookmark_count" : { "$first": "$bookmark_count" },
                  }
              },{ '$lookup':
                   {
                      'from': 'bookmark_model',
                      'localField': "_id",
                      'foreignField': "project_id",
                      'as': "bookmarks"
                  }
              },
            ]
            
            projects = list(ProjectModel.objects.aggregate(*pipeline))
            projects = json.loads(dumps(projects))
            for project in projects:
                project['bookmark_count'] = project.get('bookmark_count', 0)
                if project.get('bookmarks', False):
                    bookmarks_count = project.get('bookmark_count', 0) if project.get('bookmark_count', 0) else 0
                    project['bookmark_count'] = bookmarks_count + len(project.get('bookmarks', []))

            response = projects

        except Exception as e:
            response = "Bad Request"
            print(e)
        return response
