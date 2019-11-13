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

class User(Resource):
    # @requires_auth
    def get(self, slug_or_id):
        try:
            # user = UserModel.objects(
            #     # legacy_id=user_id,
            #     email=email
            # ).modify(set_on_insert__tags_followed=[],
            #     upsert=True, new=True)

        
            query = {
                '$or': [
                    {'slug': slug_or_id},
                    {'email': slug_or_id},
                ]
            }
            try:
                legacy_id = int(slug_or_id)
                query = {
                    'legacy_id': legacy_id
                }
            except:
                try:
                    oid = bson.objectid.ObjectId(slug_or_id)
                    query = {
                        '_id': oid
                    }
                except:
                    pass
                pass
            user = UserModel.objects.get(
               __raw__=query
            )
            json_user = json.loads(user.to_json())

            query = {
                'name': {'$in': user['tags_followed']}
            }
            tags = TagModel.objects(__raw__=query)
            json_user['tags_followed'] = json.loads(tags.to_json())

            if json_user.get('email'):
                json_user['email'] = None
            response = flattenOID(json_user)
        except Exception as e:
            print(e)
            response = Response('Could not read user object', 400)
        return response

    # @requires_auth
    # def post(self, slug):
    #     print(g.current_user)
    #     if not g.current_user:
    #         return {'message': 'Not authorized'}, 401
    #     try:
    #         first_name = request.json.get('first_name')
    #         last_name = request.json.get('last_name')
    #         email = slug
    #         full_name = '{} {}'.format(first_name, last_name)
    #         actual_slug = generate_user_slug(full_name)
    #         try:
    #             existingUser = UserModel.get(slug=actual_slug)
    #             if existingUser:
    #                 actual_slug = '{}.{}'.format(actual_slug, id_generator())
    #         except:
    #             print('DoesNotExist')
    #             pass

    #         user = UserModel.objects(
    #             email=email
    #         ).modify(
    #             set_on_insert__tags_followed=[],
    #             set__first_name=request.json.get('first_name'),
    #             set__last_name=request.json.get('last_name'),
    #             set_on_insert__slug=actual_slug,
    #             set__auth0_id=g.current_user.get('sub'),
    #             upsert=True,
    #             new=True
    #         )
    #         return json.loads(user.to_json())
    #     except Exception as e:
    #         print(e)
    #         return 's'

    @requires_auth
    def put(self, slug_or_id):

        if not g.current_user:
            return {'message': 'Not authorized'}, 401

        userSettings = request.json 
        try:
            query = {
                '_id': bson.objectid.ObjectId(g.current_user.get('user_id', None))
            }
            user = UserModel.objects.get(__raw__=query)
        except UserModel.DoesNotExist as e:
            abort(400)
            # user.legacy_id = user_id

        user.notify_toggle = userSettings.get('notify_toggle', False)
        user.accepts_cookies = userSettings.get('accepts_cookies', False)
        user.company_profile = userSettings.get('company_profile', False)
        user.picture = userSettings.get('picture', None)
        user.bio = userSettings.get('bio', None)
        user.website = userSettings.get('website', None)
        user.location = userSettings.get('location', None)
        user.profession = userSettings.get('profession', None)

        user.twitter = userSettings.get('twitter', None)
        user.linkedin = userSettings.get('linkedin', None)
        user.facebook = userSettings.get('facebook', None)
        user.instagram = userSettings.get('instagram', None)

        user.save()
        response = json.loads(user.to_json())
        return response


def generate_user_slug(s):
    slug = re.sub('[^0-9a-zA-Z-_]+', '.', s)
    return slug.lower()
