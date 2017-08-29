import requests
import configparser
import time
import praw
import prawcore
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
	
def replytopost(submission, gfy_name):
    url = 'https://www.gfycat.com/' + gfy_name
    #message = '(gfycat)[{}]'.format(url)
    message = "[Gfycat Url]({})\n\n" \
                "***\n\n" \
                "^Why ^am ^I ^mirroring ^to ^gfycat? ^Because ^work ^blocks ^streamables".format(url)
    while True:
        try:
            submission.reply(message)
            print('commented!')
            break
        except praw.exceptions.APIException as e:
            print('hit rate limit ' + e.message)
            time.sleep(60)
            continue
        except prawcore.exceptions.Forbidden as e: # probably banned if I get this
            print('praw exception ' + e.message)
            break
        except:
            break

def streamable_length(streamable_url):
    r = requests.get(streamable_url)
    soup = BeautifulSoup(r.text,'lxml')

    html =  soup.find_all('script')
    html_len = len(html) -3

    streamable_len = html[html_len]['data-duration']

    streamable_len = float(streamable_len)

    return streamable_len
	
def main():
    subreddit = reddit.subreddit('pubattlegrounds')
    old_ids = []
    # for refresh token
    start_time = time.time()
    while True:
        try:
            if time.time() - start_time >= 3300:
                gfy_instance.reauthorize_me()
                start_time = time.time()

            for submission in subreddit.hot(limit=30):
                if re.search('streamable', submission.url) != None and submission.id not in old_ids:
                    gfy_name = upload(submission.title, submission.url)

                    if check_status(gfy_name) == 'complete':
                        old_ids.append(submission.id)
                        replytopost(submission, gfy_name)
						
            print('sleeping 5 minutes\n')
            time.sleep(300)
        except prawcore.exceptions.ServerError:
            print('error with praw, sleeping then restarting')
            time.sleep(10)
            continue


reddit = praw_auth()
gfy_instance = gfy_auth()

if __name__ == '__main__':
    main()
