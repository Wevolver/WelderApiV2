from flask_restful import Resource
from flask import request
import json
from auth.decorators import requires_permission_to
from resources.models import *
from auth.auth0 import AuthError, requires_auth
from flask import g
import string
import random
import re
from utils.mongoUtils import flattenOID
from utils.mailchimp import mailchimp_add_to_signup_list

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def generate_user_slug(s):
    slug = re.sub('[^0-9a-zA-Z-_]+', '.', s)
    return slug.lower()


class Users(Resource):
    def get(self):
        try:
            query = {
                'notify_toggle': True
            }
            users = UserModel.objects(__raw__=query)
            response = json.loads(users.to_json())
        except Exception as e:
            print(e)
            response = "Couldn't find any users"
        return response


    @requires_auth
    def post(self):
        if not g.current_user:
            return {'message': 'Not authorized'}, 401
        try:
            first_name = request.json.get('first_name')
            last_name = request.json.get('last_name')
            legacy_id = request.json.get('legacy_id', None)
            email = request.json.get('email')
            full_name = '{} {}'.format(first_name, last_name)
            actual_slug = generate_user_slug(full_name)
            user = None
            isNewUser = False
            try:
                user = UserModel.objects.get(email=email)
            except:
                user = UserModel(email=email)
                isNewUser = True
                pass
            if user.slug == None:
                try:
                    existingUser = UserModel.objects.get(slug=actual_slug)
                    if existingUser:
                        actual_slug = '{}.{}'.format(actual_slug, id_generator())
                except Exception as e:
                    print('DoesNotExist')
                    pass
                user.slug = actual_slug
            user.first_name = request.json.get('first_name')
            user.last_name = request.json.get('last_name')

            if user.auth0_id == None:
                try:
                    mailchimp_add_to_signup_list(user.email, user.first_name, user.last_name)
                except:
                    pass
            if legacy_id:
                user.legacy_id = legacy_id

            user.auth0_id = g.current_user.get('sub')
            user.save()

            response = json.loads(user.to_json())
            if isNewUser:
                response['isNewUser'] = True
            return flattenOID(response)
        except Exception as e:
            print(e)
            return 'something went wrong'
