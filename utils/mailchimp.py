from flask import current_app as app
import requests

LIST_ID = ''

def mailchimp_endpoint_url(endpoint):
    '''
        Format an endpoint in a full mailchimp api url
            >   mailchimp_endpoint_url('/lists', region='us2', version='3.0')
            >>  https://us2.api.mailchimp.com/3.0/lists
    '''

    return 'https://us2.api.mailchimp.com/3.0/{endpoint}'.format(
        endpoint=endpoint.lstrip('/')
    )

def mailchimp_add_to_signup_list(email, first_name, last_name):
    API_KEY = app.config.get('MAILCHIMP_KEY', None)
    if API_KEY and email:
        endpoint = 'lists/{id}/members'.format(id=LIST_ID)
        endpoint_url = mailchimp_endpoint_url(endpoint)
        auth = ('-', API_KEY)
        payload = {
            'email_address': email,
            'status': 'subscribed',
            'merge_fields': {
                'FNAME': first_name,
                'LNAME': last_name
            }
        }
        requests.post(endpoint_url, json=payload, auth=auth)
