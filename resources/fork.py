from flask_restful import Resource
from flask import request
from flask import g
import logging
import json

logger = logging.getLogger()


class Fork(Resource):
    with open("resources/plans.json") as data_file:
        plans = json.loads(data_file.read())

    def post(self, id):
        """
        Grabs the project from the database and updates it with whatever values
        are sent in the request.
        """

        try:
            project = g.db.get_item(Key={'project_id': id})['Item']
            data = request.json
            for key, value in data.items():
                project[key] = value
            response = g.db.put_item(Item=project)
        except Exception as inst:
            response = "Couldn't update this project"
            logger.info((inst))
        return response
