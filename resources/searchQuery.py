from flask import current_app as app
from flask_restful import Resource
from resources.models import *
from flask import Response
from flask import request
from datetime import datetime
import requests
import json


class SearchQuery(Resource):
    def post(self):
        try:
            search = request.json
            query = search.get('query', None)
            if not query:
                error_message = json.dumps({'Query': "No query"})
                return Response(error_message, 401)
            search_query = {'query': query, 'date_searched': datetime.utcnow()}
            search_query_model = SearchModel(**search_query)
            search_query_model.save()
            search_key = app.config.get('SEARCH_KEY')
            results = requests.get('https://www.googleapis.com/customsearch/v1?key={}&q={}'.format(search_key, query))
            search_results = [
                {
                    'title': result['title'],
                    'link': result['link'],
                    'html_title': result['htmlTitle'],
                    'html_snippet': result['htmlSnippet'],
                    'description': result['pagemap']['metatags'][0].get('og:description', ""),
                    'image': result['pagemap']['metatags'][0].get('og:image', ""),
                }
                for result in results.json()['items']
            ]
            return search_results
        except Exception as e:
            print(e)
            error_message = json.dumps({'Query': query})
            return Response(error_message, 401)
