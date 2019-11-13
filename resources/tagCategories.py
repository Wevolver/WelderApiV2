from flask_restful import Resource
from resources.models import *
from flask import request, Response
import itertools
import json
import time
from bson.json_util import dumps, default


class TagCategories(Resource):
    def get(self):
        try:
            category = request.args.get('category')
            if category:
                query = {'name': category}
                category_object = TagCategoryModel.objects.get(__raw__=query)

                query = {
                    'name': {'$in': category_object.relatedTags},
                }
                tagged = TagModel.objects(__raw__=query)
                relatedTags = []
                for key in category_object.relatedTags:
                    tagObject = { 'name': key }
                    if tagged(name=key) and tagged(name=key)[0].displayName:
                        tagObject['displayName'] = tagged(name=key)[0].displayName
                    relatedTags.append(tagObject)

                category_object.relatedTags = relatedTags
                response = json.loads(category_object.to_json())
            else:
                pipeline = [
                    { "$unwind": "$relatedTags" },
                    { "$lookup": {
                           "from": "tag",
                           "localField": "relatedTags",
                           "foreignField": "name",
                           "as": "tagObjects"
                        }
                    },
                    { "$unwind": "$tagObjects" },
                    { "$group": {
                            "_id": "$_id",
                            "name": { '$first': "$name"},
                            "active": { '$first': "$active"},
                            "relatedTags": { "$push": "$tagObjects" },
                            "searchTags": { "$first": "$searchTags" }

                        }
                    }
                ]
                categories = TagCategoryModel.objects.aggregate(*pipeline)
            return Response(dumps(categories, default=default), mimetype='application/json')
        except Exception as e:
            print(e)
            return "Couldn't retreive categories"

    def post(self):
        try:
            category = request.json
            searchTags = category.get('searchTags')
            relatedTags = category.get('relatedTags')
            if not searchTags or not relatedTags:
                return "No tags were received"
            category['searchTags'] = [tag.name for tag in TagModel.objects() if tag.name in searchTags]
            category['relatedTags'] = [tag.name for tag in TagModel.objects() if tag.name in relatedTags]
            category['active'] = category.get('active', True)
            category_model = TagCategoryModel(**category)
            category_model.save()
            return category
        except Exception as e:
            print(e)
            return "Couldn't create category"

    def put(self):
        try:
            new_category = request.json
            if new_category:
                query = {'name': new_category.get('name')}
                category_object = TagCategoryModel.objects.get(__raw__=query)
                if new_category.get('relatedTags'):
                    category_object.relatedTags = new_category.get('relatedTags')
                if new_category.get('searchTags'):
                    category_object.searchTags = new_category.get('searchTags')
                if new_category.get('active') == True or  new_category.get('active') == False:
                    category_object.active = new_category.get('active')
                category_object.save()
                response = json.loads(category_object.to_json())
            else:
                response = "Category was not found"
            return response
        except Exception as e:
            return "Couldn't update category"

    def delete(self):
        try:
            response = "Could not delete category"
            category = request.args.get('category')
            if category:
                query = {'name': category}
                category_object = TagCategoryModel.objects.get(__raw__=query)
                category_object.delete()
                response = {"deleted": json.loads(category_object.to_json())}
            return response
        except Exception as e:
            return "Couldn't delete category"
