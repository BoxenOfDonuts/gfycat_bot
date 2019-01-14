import requests
import time
from logger import logger

auth_url = 'https://api.gfycat.com/v1/oauth/token'
upload_url = 'https://api.gfycat.com/v1/gfycats'
root_status_url = 'https://api.gfycat.com/v1/gfycats/fetch/status/'
root_check_link_url = 'http://gfycat.com/cajax/get/'
root_update_gfy_url = 'https://api.gfycat.com/v1/me/gfycats/'
root_md5_url = 'http://gfycat.com/cajax/checkUrl/'


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

            logger.info('retrieved gfycat access token')
        except requests.exceptions.RequestException as e:
            logger.info('could not authenticate to gfycat')

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
            logger.info('retrieved access token')
        except requests.exceptions.RequestException as e:
            logger.error('could not get authenticate')

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
            logger.info('refreshed access token')
        except requests.exceptions.RequestException as e:
            logger.error('could not authenticate')

    def upload_from_file(self, file, **kwargs):
        self.file = file
        title = kwargs.get('title',None)
        start  = kwargs.get('start',None)
        duration  = kwargs.get('duration',None)
        tags = kwargs.get('tags',None)

        upload_dict = {
            'fetchUrl':url
        }
        if title != None:
            upload_dict.update({'title':title})
        if tags != None:
            upload_dict.update({'tags':tags})

        header = {'Authorization': self.access_token, 'Content-Type': 'application/json'}

        try:
            r = requests.post('https://api.gfycat.com/v1/gfycats',headers=header,json=upload_dict)
            key = r.json()['gfyname']
        except requests.exceptions.RequestException as e:
            logger.error('could not get key')
            logger.error('exception', extra={'error': e})
            return

        try:
            r = requests.post('https://filedrop.gfycat.com',files={'file': open(file,'rb')},data={'key':key})
        except requests.exceptions.RequestException as e:
            logger.error('could not upload file', extra={'error': e})

        time.sleep(5)
        try:
            status_url = root_status_url + key
            r = requests.get(status_url)
            if r.json()['md5Found'] == 1:
                key = r.json()['gfyname']
                logger.info('md5 found, using that name')
            else:
                logger.error('no key found')
        except requests.exceptions.RequestException as e:
            logger.error('something went wrong', extra={'error': e})

        return key

    def upload_from_url(self, url, **kwargs):
        self.url = url
        title = kwargs.get('title',None)
        start = kwargs.get('start',None)
        duration = kwargs.get('duration',None)
        tags = kwargs.get('tags',None)

        upload_dict = {
            'fetchUrl':url
        }
        if title != None:
            upload_dict.update({'title':title[:120]})
        if start != None:
            upload_dict.update({'cut':{'duration':duration,'start':start}})
        if tags != None:
            upload_dict.update({'tags':tags})

        header = {'Authorization': self.access_token, 'Content-Type': 'application/json'}

        try:
            r = requests.post(upload_url, headers=header, json=upload_dict)
            key = r.json()['gfyname']
            logger.info('upload sucessfull')
        except requests.exceptions.RequestException as e:
            logger.error('could not fetch url', extra={'error': e})

        return key

    def check_status(self, key):
        status_url = root_status_url + key
        try:
            r = requests.get(status_url)
            response = r.json()['task']

            if response == "encoding":
                logger.info('encoding', extra={'gfycname': key})
            elif response == 'complete':
                logger.info('gfycat complete!', extra={'gfyname': key})
            elif response == 'NotFoundo':
                logger.error('gfycat not found, something went wrong', extra={'gfyname': key})
            elif response == 'error':
                logger.error('Something went wrong uploading url', extra={'gfyname': key})
            else:
                logger.error('unknown status', extra={'gfyname': key})
                response = 'error'
        except requests.exceptions.RequestException as e:
            logger.error('could not fetch url', extra={'error': e})
            response = 'error'

        return response

    def delete_gfy(self, key):
        # need gfyname, not link
        url = root_update_gfy_url + key
        header = {'Authorization': self.access_token, 'Content-Type': 'application/json'}
        try:
            r = requests.delete(url, headers=header)
            # no response if sucessful, so if I get something back its an error
            if r.text:
                return r.json()['errorMessage']['description']
            else:
                logger.info("Deleted Gfy")
        except requests.exceptions.RequestException as e:
            logger.error('error', extra={'error': e})

    def check_gfy(self, key):
        # need gfyname, not full link
        url = root_check_link_url + key
        try:
            r = requests.get(url)
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error('error getting url', extra={'error': e})

    # Don't think this works anymore
    def check_url(self, url):
        formated_url = requests.utils.quote(url)
        url = root_md5_url + formated_url
        try:
            r = requests.get(url)
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error('error', extra={'error': e})

