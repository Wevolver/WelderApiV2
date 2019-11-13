from flask import current_app as app
from auth.decorators import requires_permission_to
from flask_restful import Resource
from resources.models import *
from datetime import datetime
from flask import Response
from flask import request
import bleach
import requests
import json
import bson
from auth.auth0 import AuthError, requires_auth
from flask import g

class Comment(Resource):
    @requires_auth
    def post(self, discusses_id):
        if not g.current_user:
            return {'message': 'Not authorized'}, 401
        try:
            sent_comment = request.json.get('comment')
            if not sent_comment:
                return {'message': 'Not authorized'}, 401

            text = sent_comment.get('text', None)
            if not text:
                return {'message': 'Empty comment'}, 400

            query = {
                '_id': bson.objectid.ObjectId(discusses_id),
            }
            project = ProjectModel.objects.get(__raw__=query)

            sent_comment['discusses'] = project.id
            sent_comment['dateCreated'] = datetime.utcnow()
            sent_comment['text'] = bleach.clean(text, strip=True)
            new_comment = CommentModel(**sent_comment)
            new_comment.save()
            response = json.loads(new_comment.to_json())
            return response
        except Exception as e:
            print(e)
            error_message = json.dumps({'Query': query})
            return Response(error_message, 401)

    def get(self, discusses_id):
        try:
            query = {
                'discusses': bson.objectid.ObjectId(discusses_id),
            }
            comments = CommentModel.objects(__raw__=query).order_by('dateCreated')
            return json.loads(comments.to_json())
        except Exception as e:
            print(e)
            error_message = json.dumps({'Message': 'Nothing to see here.'})
            return Response(error_message, 401)
