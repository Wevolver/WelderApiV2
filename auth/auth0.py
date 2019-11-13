import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from flask import g

AUTH0_DOMAIN = 'welder.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'http://localhost:5000/api/v2'


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get('Authorization', None)
    if not auth:
        return None, None

    token = auth.split(':')[0]
    try:
        user_id = auth.split(':')[1]
    except Exception as e:
        user_id = None

    parts = token.split()

    if len(parts) == 1 and parts[0] != 'bearer':
        return parts[0], user_id
    elif parts[0].lower() != 'bearer':
        return None, user_id
    elif len(parts) > 2:
        return None, user_id

    token = parts[1]
    if token == '-':
        return None, user_id
    return token, user_id


def requires_auth(f):
    """Determines if the Access Token is valid
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token, user_id = get_token_auth_header()
        _request_ctx_stack.top.current_user = None
        g.current_user={}
        if user_id:
             g.current_user['user_id'] = user_id
        if token:
            jsonurl = urlopen('https://{}/.well-known/jwks.json'.format(AUTH0_DOMAIN))
            jwks = json.loads(jsonurl.read().decode('utf-8'))
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    rsa_key = {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
            if rsa_key:
                try:
                    payload = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=ALGORITHMS,
                        audience=API_AUDIENCE,
                        issuer='https://' + AUTH0_DOMAIN + '/'
                    )
                    payload['user_id'] = user_id
                except jwt.ExpiredSignatureError:
                    raise AuthError({
                        'code': 'token_expired',
                        'description': 'Token expired.'
                    }, 401)

                except jwt.JWTClaimsError:
                    raise AuthError({
                        'code': 'invalid_claims',
                        'description': 'Incorrect claims. Please, check the audience and issuer.'
                    }, 401)
                except Exception as e:
                    raise AuthError({
                        'code': 'invalid_header',
                        'description': 'Unable to parse authentication token.'
                    }, 400)
                _request_ctx_stack.top.current_user = payload
                g.current_user = payload
        return f(*args, **kwargs)

    return decorated
