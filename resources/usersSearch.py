from flask_restful import Resource
from flask import request, Response
from flask import request
from auth.decorators import requires_permission_to
from resources.models import *
import json
from auth.auth0 import AuthError, requires_auth
from flask import g
import re
from utils.mongoUtils import flattenOID
import bson

class UsersSearch(Resource):
    # @requires_auth
    def get(self):
        try:
            search = request.args.get('name', None)
            if search:
                search = generate_user_slug(search)
                regex = re.compile('.*{}.*'.format(search))
                users = UserModel.objects(slug=regex)[:4]
                return json.loads(users.to_json())
            else:
                return []
        except Exception as e:
            print(e)
            response = Response('Could not read user object', 400)
        return response

def generate_user_slug(s):
    slug = re.sub('[^0-9a-zA-Z-_]+', '.', s)
    return slug.lower()