from flask_restful import Resource
from resources.models import *
from flask import request
import logging
import stream
import json

logger = logging.getLogger()
client = stream.connect('', '', location='us-east')

class Activity(Resource):
    def post(self):

        data = request.json
        members = data.get('project', None)
        committer = data.get('user', None)
        project = data.get('project_name', None)

        try:
            query = {'user_slug': committer , 'slug': project}
            project = ProjectModel.objects.get(__raw__=query)
            members = [member.get('id') for member in project.members]
            for member in members:
                user_feed = client.feed('users', member)
                activity_data = {
                    "actor": committer,
                    "verb": "committed",
                    "object": project.name,
                }
                activity_response = user_feed.add_activity(activity_data)
        except Exception as e:
            print(e)
