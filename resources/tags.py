from auth.decorators import requires_permission_to
from flask_restful import Resource
from flask import request
import json
import bson
import operator
# from auth.decorators import requires_permission_to
from resources.models import *
import logging
import bson
from auth.auth0 import requires_auth
from flask import g
from bson.json_util import dumps

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Tags(Resource):
    def get(self):
        if request.args.get('options', None):
            options = request.args.get('options', None)
            query = {'weight': {'$ne':0}}
            if options == 'all':
                query = {}
                tags = TagModel.objects(__raw__=query).order_by('name')
            elif options == 'search':
                query = {'weight': {'$ne': -1}}
                tags = TagModel.objects(__raw__=query).order_by('name')
            else:
                query = {'name': options}
                tags = TagModel.objects(__raw__=query).order_by('name')
            return json.loads(tags.to_json())
        response = "nothing"

        try:
            select_tags = request.args.get('tags', '').split(',')
            select_tags = list(filter(None, select_tags))
            related = len(select_tags) > 0
            if related:
                '''
                  find tags where the name is in the query
                  will loop through the results to find the related tags
                  and return those
                '''
                query = {
                    '$or': [
                        { 'name': { '$in': select_tags } },
                        { 'weight': 0 }
                    ]
                }
            else:
                '''
                    if there is no query just return tags (there are no related tags)
                    we will add the weight later so that the tags returned here
                    are the most general.
                '''
                query = {
                    'weight': 1,
                }

            tags = TagModel.objects(__raw__=query).limit(7)

            if related:
                setlist = []
                removeList = []
                for tag in tags:
                    if tag.weight is 0:
                        removeList.append(tag.name)
                    else:
                        setlist.append(set(tag.counts))

                # creates an array with the intersection of tag counts names (ie: related tags)
                counts_intersection = set.intersection(*setlist)
                '''
                    we need to order the resulting list by the count amount
                    which is the addition of all the count values for every selected tag
                '''
                tag_dict = {}
                # loop through the selected tags, initialize to 0
                for tag_name in counts_intersection:
                    tag_dict[tag_name] = 0

                # loop through the selected tags, and increment the count number of that tag to the tag_dict key
                for tag_name in counts_intersection:
                    for tag in tags:
                        if tag.weight is not 0:
                            tag_dict[tag_name] = tag_dict[tag_name] + tag.counts.get(tag_name, 0)
                # sort the tag list by count number
                tag_dict = sorted(tag_dict.items(), key=operator.itemgetter(1), reverse=True)
                response  = []

                '''
                    return only the name, I did it like this in case we want to return more information about the tag
                    at some point in the future
                '''


                query = {
                    'name': {'$in': [key for key, value in tag_dict[:6]]},
                }
                tagged = TagModel.objects(__raw__=query)

                for key, count in tag_dict:
                    if key not in removeList:
                        tagObject = {
                            'name': key
                        }
                        try:
                            if tagged(name=key)[0].displayName:
                                tagObject['displayName'] = tagged(name=key)[0].displayName
                        except:
                            response.append(tagObject)
                            if len(response) > 6:
                                break
            else:
                '''
                    This is only needed so that the response from this endpoint is always the same format
                    it can't be done before because the whole tag object is needed above.
                '''
                response = []
                for tag in tags:
                    response.append({'name': tag.name})
        except Exception as e:
            logger.info('Error ' + str(e))
            response = []
        return response[0:6]

    @requires_auth
    def post(self):
        if not g.current_user.get('sub', None):
            return {'message': 'Not authorized'}, 401
        response = "Could not create tags"
        body = request.json
        tags = body.get('tags', [])
        auth_user = UserModel.objects.get(auth0_id=g.current_user['sub'])
        if type(tags) is list:
            for tag in tags:
                try:
                    query = {
                        '_id': bson.objectid.ObjectId(body.get('project_id')),
                        'members': {'$elemMatch': {'id': {'$in':[auth_user.legacy_id, auth_user.id]}}}
                    }
                    project = ProjectModel.objects.get(__raw__=query)
                    project_old_tags = project.tags
                    # This is here so that we can stop the creation of new tags if we want
                    # super_secret could be replaced by some form of auth.
                    if body.get('pwd', None) == 'super_secret':
                        new_tag = TagModel.objects(name=body.get('name')).upsert_one(
                            weight=int(body.get('weight', 2)),
                            name=tag
                        )
                    else:
                        new_tag = TagModel.objects.get(name=tag)
                    if new_tag.name not in project_old_tags:
                        for old_tag_name in project_old_tags:
                            # update tags that are already in the project with a count of the new tag.
                            # upsert=true so that tags that are already in project get inserted into the collection. (for backwards comp)
                            # Note: Could be replaced by a script.
                            update = {'inc__counts__{}'.format(new_tag.name): 1, 'upsert': True}
                            TagModel.objects(name=old_tag_name).update_one(**update)
                            # update new tag counts
                            # upsert=false since we don't want random tags to be created (at least yet)
                            update = {'inc__counts__{}'.format(old_tag_name): 1, 'upsert': False}
                            TagModel.objects(name=new_tag.name).update_one(**update)
                        project.tags.append(new_tag.name)
                        project.save()

                        query = {'user_slug': project.user_slug, 'slug': project.slug}
                        pipeline = [
                            {
                                '$match': query
                            },
                            { '$limit' : 1 },
                            {'$lookup':
                                 {
                                    'from': 'tag',
                                    'localField': "tags",
                                    'foreignField': "name",
                                    'as': "tags"
                                }
                            },
                            {'$lookup':
                                 {
                                    'from': 'bookmark_model',
                                    'localField': "_id",
                                    'foreignField': "project_id",
                                    'as': "bookmarks"
                                }
                            }
                        ]
                        return_project = list(ProjectModel.objects.aggregate(*pipeline))[0]
                    response = json.loads(dumps(return_project))
                except Exception as e:
                    print(e)
                    response = 'Tag already exists or could not be found'

        return response

    @requires_auth
    def delete(self):
        # delete tag from project and update tag counts
        body = request.json
        response = 'Could not delete tag'
        if not g.current_user.get('sub', None):
            return {'message': 'Not authorized'}, 401
        auth_user = UserModel.objects.get(auth0_id=g.current_user['sub'])
        try:
            query = {
                '_id': bson.objectid.ObjectId(body.get('project_id')),
                'members': {'$elemMatch': {'id': {'$in':[auth_user.legacy_id, auth_user.id]}}}
            }
            project = ProjectModel.objects.get(__raw__=query)
            project_old_tags = project.tags
            new_tag = TagModel.objects.get(name=body.get('name'))
            if new_tag.name in project_old_tags:
                project_old_tags.remove(new_tag.name)
                for old_tag_name in project_old_tags:

                    update = {'inc__counts__{}'.format(new_tag.name): -1, 'upsert': False}
                    TagModel.objects(name=old_tag_name).update_one(**update)

                    update = {'inc__counts__{}'.format(old_tag_name): -1, 'upsert': False}
                    TagModel.objects(name=new_tag.name).update_one(**update)

                project.save()
                query = {'user_slug': project.user_slug, 'slug': project.slug}
                pipeline = [
                    {
                        '$match': query
                    },
                    { '$limit' : 1 },
                    {'$lookup':
                         {
                            'from': 'tag',
                            'localField': "tags",
                            'foreignField': "name",
                            'as': "tags"
                        }
                    },
                    {'$lookup':
                         {
                            'from': 'bookmark_model',
                            'localField': "_id",
                            'foreignField': "project_id",
                            'as': "bookmarks"
                        }
                    }
                ]
                return_project = list(ProjectModel.objects.aggregate(*pipeline))[0]
            response = json.loads(dumps(return_project))
        except Exception as e:
            print(e)
        return response
