from flask import request
from functools import wraps
import json
import requests
import logging
import jwt

logger = logging.getLogger(__name__)


def requires_permission_to():
    def has_permission(func):
        @wraps(func)
        def _decorator(*args, **kws):
            auth_user = None
            token = request.headers.get('Authorization', None)
            if token:
                decoded = decode_token(token)
                if decoded and decoded['user']:
                    auth_user = decoded['user']
            return(func(auth_user, *args, **kws))
        return _decorator
    return has_permission


def decode_token(token):
    try:
        with open('./auth/jwt.verify', 'r') as verify:
            try:
                return jwt.decode(
                    token,
                    verify.read(),
                    algorithms=['RS256'],
                    issuer='wevolver')
            except jwt.ExpiredSignatureError as error:
                print(error)
                return None
    except Exception as e:
        print(e)
        return None
