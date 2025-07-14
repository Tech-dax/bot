import requests
from urllib.parse import urlencode


class FacebookOAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = 'https://graph.facebook.com/v15.0'

    def get_authorize_url(self, scopes):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ','.join(scopes),
        }
        return f"https://www.facebook.com/v15.0/dialog/oauth?{urlencode(params)}"

    def get_access_token(self, code):
        url = f'{self.base_url}/oauth/access_token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        print(f'request_url : {url}?{params}')
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('access_token')


    def get_user_pages(self, access_token):
        url = f'{self.base_url}/me/accounts'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
