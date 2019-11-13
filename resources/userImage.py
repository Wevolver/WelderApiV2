from flask import current_app as app
from flask_restful import Resource
from flask import request
import requests
import logging
import boto3

logger = logging.getLogger()

class UserImage(Resource):

    def get(self):
        """
        get a presigned url
        """

        s3 = boto3.client('s3')

        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': 'wevolver-user-images',
                'Key': request.args.get('objectName'),
                'ContentType': request.args.get('contentType'),
                'ACL': 'public-read'
            }
        )

        url = {"signedUrl": url}
        return url
