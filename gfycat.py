import requests

auth_url = 'https://api.gfycat.com/v1/oauth/token'
upload_url = 'https://api.gfycat.com/v1/gfycats'
root_status_url = 'https://api.gfycat.com/v1/gfycats/fetch/status/'
root_check_link_url = 'http://gfycat.com/cajax/get/'
root_update_gfy_url = 'https://api.gfycat.com/v1/me/gfycats/'

'''
class AuthWrapper(object):
    def __init__(self, client_id, client_secret, username, password):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.refresh_token = None

        if client_id is None:
            raise TypeError('client id required')
        if client_secret is None:
            raise TypeError('client secret is required')
'''


class GfyClient(object):
    def __init__(self, client_id, client_secret, username, password):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.refresh_token = None
        self.access_token = None

        if client_id is None:
            raise TypeError('client id required')
        if client_secret is None:
            raise TypeError('client secret is required')

    def authorize_me(self):

        oauth = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }
        try:
            r = requests.post(auth_url, json=oauth)
            self.access_token = r.json()['access_token']
            self.refresh_token = r.json()['refresh_token']
            print('retrieved access token')
        except r.status_code != 200:
            print('could not get authenticate')


    def reauthorize_me(self):
        # to be implemented

        oauth = {
            "grant_type": "refresh",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }

        try:
            r = requests.post(auth_url, json=oauth)
            self.access_token = r.json()['access_token']
            self.refresh_token = r.json()['refresh_token']
            print('refreshed access token')
        except r.status_code != 200:
            print('could not authenticate')


    def upload_from_url(self, url, title, start, duration):
        self.url = url
        self.title = title
        self.start = start
        self.duration = duration

        upload_dict = {
            'fetchUrl': url,
            'title': title,
            'tags': ['PUBG', 'Battlegrounds', 'PUBATTLEGOUNDS'],
            'cut': {'duration': duration, 'start': start}
        }

        header = {'Authorization': self.access_token, 'Content-Type': 'application/json'}

        try:
            r = requests.post(upload_url, headers=header, json=upload_dict)
            key = r.json()['gfyname']
            print('upload complete')
        except r.status_code != 200:
            print('could not fetch url')

        return key

    def check_status(self, key):
        status_url = root_status_url + key
        try:
            r = requests.get(status_url)
            response = r.json()['task']

            if response == "encoding":
                print('encoding')
            elif response == 'complete':
                print('gfycat complete! Gfyname: {}'.format(key))
            elif response == 'NotFoundo':
                print('gfycat not found, something went wrong')
            elif response == 'error':
                print('Something went wrong uploading url')
            else:
                print('unknwn status')
                response = 'error'
        except r.status_code != 200:
            print('could not fetch url')
            response = 'error'

        return response

    def delete_gfy(self, key):
        url = root_update_gfy_url + key
        header = {'Authorization': self.access_token, 'Content-Type': 'application/json'}

        try:
            r = requests.delete(url, headers=header)
            print('gfy deleted')
        except r.status_code != 200:
            print('error')

    def check_link(self, key):
        url = root_check_link_url + key
        try:
            r = requests.get(url)
        except r.status_code != 200:
            print('error getting url')
