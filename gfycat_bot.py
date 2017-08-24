import requests
import configparser
import time
import praw
import re
from bs4 import BeautifulSoup
import gfycat

def gfy_auth():
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini')

    gfy_instance = gfycat.GfyClient(client_id = config['gfycat']['client_id'],
        client_secret = config['gfycat']['client_secret'],
        username = config['gfycat']['username'],
        password = config['gfycat']['password']
    )
    gfy_instance.authorize_me()
    return gfy_instance


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
        "refresh_token": refresh_token
    }

    r = requests.post(auth_url, json=oauth)
    access_token = r.json()['access_token']
    refresh_token = r.json()['refresh_token']
    print('refreshed access token')
    
    return access_token,refresh_token


def upload(title, url):
    duration = streamable_length(url)
    if duration > 60:
        start = duration - 60
        duration = 60
    else:
        start = 0

    key = gfy_instance.upload_from_url(url=url,title=title,duration=duration,start=start)

    return key


def check_status(key):
    response = gfy_instance.check_status(key)
    while response != 'complete':
        time.sleep(15)
        response = gfy_instance.check_status(key)
        if response == 'encoding':
            continue
        elif response == 'error' or not response:
            break
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
    soup = BeautifulSoup(r.text,'lxml')

    thing =  soup.find_all('script')
    thing_len = len(thing) -3

    time = thing[thing_len]['data-duration']

    time = float(time)

    return time

def main():
    subreddit = reddit.subreddit('pubattlegrounds')
    old_ids = []
    # for refresh token
    start_time = time.time()
    while True:

        if time.time() - start_time >= 55:
            gfy_instance.reauthorize_me()

        for submission in subreddit.hot(limit=30):
            if re.search('streamable', submission.url) != None and submission.id not in old_ids:
                gfy_name = upload(submission.title, submission.url)

                if check_status(gfy_name) == 'complete':
                    sendmessage(submission.title, submission.url, submission.shortlink, gfy_name)
                    # replytopost(submission,

                old_ids.append(submission.id)

        print('sleeping 5 minutes\n')
        catpictures()
        time.sleep(300)


reddit = praw_auth()
gfy_instance = gfy_auth()

if __name__ == '__main__':
    main()