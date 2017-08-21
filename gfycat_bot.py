import requests
import configparser
import time
import praw
import re
from bs4 import BeautifulSoup
from math import ceil

def gfy_auth():
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini')
    auth_url = 'https://api.gfycat.com/v1/oauth/token'
    print('getting access token..')

    oauth = {
        "grant_type": "password",
        "client_id": config['gfycat']['client_id'],
        "client_secret": config['gfycat']['client_secret'],
        "username": config['gfycat']['username'],
        "password": config['gfycat']['password']
    }

    r = requests.post(auth_url, json=oauth)
    access_token = r.json()['access_token']
    refresh_token = r.json()['refresh_token']
    print('retrieved access token')
    
    return access_token,refresh_token


def praw_auth():
    config = configparser.ConfigParser()
    config.read('config.ini')
    reddit = praw.Reddit(client_id=config['praw']['client_id'],
                 client_secret=config['praw']['client_secret'],
                 user_agent='python:nourl:v0.01 by /u/BoxenOfDonuts',
                 username=config['praw']['username'],
                 password=config['praw']['password'])
    print('logged into praw')
    return reddit


def refresh_gfy_token(refresh_token):
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini')
    auth_url = 'https://api.gfycat.com/v1/oauth/token'
    print('refreshing access token..')

    oauth = {
        "grant_type": "refresh",
        "client_id": config['gfycat']['client_id'],
        "client_secret": config['gfycat']['client_secret'],
        "refresh_token": refresh_token,
    }

    r = requests.post(auth_url, json=oauth)
    access_token = r.json()['access_token']
    refresh_token = r.json()['refresh_token']
    print('refreshed access token')
    
    return access_token,refresh_token


def upload(access_token, title, url):
    upload_url = 'https://api.gfycat.com/v1/gfycats'
    duration = streamable_length(url)
    if duration > 60:
        start = duration - 60
    else:
        start = 0

    upload_dict = {
        'fetchUrl': url,
        'title': title,
        'tags': ['PUBG', 'Battlegrounds', 'PUBATTLEGOUNDS'],
        'cut': {'duration': duration, 'start': start}
    }

    header = {'Authorization': access_token, 'Content-Type': 'application/json'}

    try:
        r = requests.post(upload_url, headers=header, json=upload_dict)
        key = r.json()['gfyname']
        print('upload complete')
    except r.status_code != 200:
        print('could not fetch url')

    return key


def check_status(key):
    root_status_url = 'https://api.gfycat.com/v1/gfycats/fetch/status/'
    status_url = 'https://api.gfycat.com/v1/gfycats/fetch/status/{}'.format(key)
    
    try:
        r = requests.get(status_url)
        response = r.json()['task']

        while response != 'complete':
            r = requests.get(status_url)
            response = r.json()['task']

            if response == "encoding":
                print('encoding')
                time.sleep(30)
                continue
            elif response == 'complete':
                print('gfycat complete! Gfyname: {}'.format(key))
            elif response == 'NotFoundo':
                print('gfycat not found, something went wrong')
                break
            elif response == 'error':
                print('Something went wrong uploading url')
                break
            else:
                print('unknwn status')
                response = 'error'
                break
    except r.status_code != 200:
        print('could not fetch url')

    return response


def catpictures():
    print("\
   |\      _,,,---,,_\n\
   /,`.-'`'    -.  ;-;;,_\n\
  |,4-  ) )-,_..;\ (  `'-'\n\
 '---''(_/--'  `-'\_)")


def sendmessage(title, url, shortlink, gfy_name):
    gfy_url = 'https://www.gfycat.com/' + gfy_name # temporary
    print('sending message')
    message = 'Title: {} URL: {} Comment URL: {} gfycat: {}'.format(title, url, shortlink, gfy_url)
    reddit.redditor('BoxenOfDonuts').message('link', message)


def replytopost(submission, gfy_name):
    url = 'https://www.gfycat.com/' + gfy_name
    message = '(gfycat)[{}]'.format(url)
    submission.reply(message)


def streamable_length(streamable_url):
    r = requests.get(streamable_url)
    soup = BeautifulSoup(r.text)

    thing =  soup.find_all('script')
    thing_len = len(thing) -3

    time = thing[thing_len]['data-duration']
    
    '''
    without import math
    if int(float(str_time)) == round(str_float(time)):
        time = int(float(str_time))
    else:
        time = int(float(str_time))+1
       
    with  math
    time = ceil(float(time))
    '''

    time = float(time)

    return time

def main(reddit):
    subreddit = reddit.subreddit('pubattlegrounds')
    old_ids = []
    start_time = time.time()
    while True:
        if time.time() - start_time => 59:
            gfy_instance,refresh_token = refresh_gfy_token(refresh_token)
            
        for submission in subreddit.hot(limit=30):
            if re.search('streamable', submission.url) != None and submission.id not in old_ids:
                gfy_name = upload(gfy_instance, submission.title, submission.url)

                if check_status(gfy_name) == 'complete':
                    sendmessage(submission.title, submission.url, submission.shortlink, gfy_name)
                    # replytopost(submission,

                old_ids.append(submission.id)

        print('sleeping 5 minutes\n')
        catpictures()
        time.sleep(300)
    # print("\033c")


reddit = praw_auth()
gfy_instance, refresh_token = gfy_auth()

if __name__ == '__main__':
    main(reddit)
