from flask import current_app as app
from flask_restful import Resource
from flask import request
import requests
import logging
import boto3
from botocore.client import Config
from editor import S3

logger = logging.getLogger()

from boto3 import Session

session = Session()
credentials = session.get_credentials()
current_credentials = credentials.get_frozen_credentials()

class ProjectImage(Resource):

    def get(self):
        """
        get a presigned url
        """

        s3 = boto3.client('s3')

        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': 'wevolver-project-images',
                'Key': request.args.get('objectName'),
                'ContentType': request.args.get('contentType'),
                'ACL': 'public-read'
            }
        )

        hash = S3.getHash({
            "keyStart": '/',
            "bucket": 'wevolver-project-images',
            "region": 'us-west-1',
            "acl": 'public-read',
            "accessKey": current_credentials.access_key,
            "secretKey": current_credentials.secret_key
        })

        url = {"signedUrl": url, "fHash": hash}
        return url
