#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import configparser
import time
import praw
import prawcore
import re
from bs4 import BeautifulSoup
import gfycat
import os


###### Globals ######

bad_list = ['jay and dan']
config = configparser.ConfigParser(interpolation=None)
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')

### end Globals #####

def gfy_auth():
    config.read(configfile)
    gfy_instance = gfycat.GfyClient(client_id = config['gfycat']['client_id'],
        client_secret = config['gfycat']['client_secret'],
        username = config['gfycat']['username'],
        password = config['gfycat']['password']
    )

    return gfy_instance


def praw_auth():
    config.read(configfile)
    reddit = praw.Reddit(client_id=config['praw']['client_id'],
                 client_secret=config['praw']['client_secret'],
                 user_agent='python:nourl:v0.01 by /u/BoxenOfDonuts',
                 username=config['praw']['username'],
                 password=config['praw']['password'])
    print('logged into praw')

    return reddit


def upload(title, url, subreddit):
    duration = streamable_length(url)
    if duration > 60:
        start = duration - 60
        duration = 60
    else:
        start = 0

    if subreddit == 'pubattlegrounds':
        tags = ['PUBG', 'Battlegrounds', 'PUBATTLEGOUNDS']
    elif subreddit == 'hockey':
        tags = ['hockey']
    elif subreddit == 'stlouisblues':
        tags = ['hockey','St. Louis Blues']

    key = gfy_instance.upload_from_url(url=url,title=title,duration=duration,start=start,tags=tags)

    return key


def check_if_commented(submisison):
    # checks the submission to see if i've commented
    for comment in submisison.comments:
        if comment.author == 'to_gfycat_bot':
            return True
        return False


def old_submission_ids():
    # retieves old submission ids that commented on
    old_ids = []
    me = reddit.redditor('to_gfycat_bot')
    for comment in me.comments.new(limit=30):
        old_ids.append(comment.submission.id)

    print('retrieved old ids')

    return old_ids


def check_status(key):
    # check status of the upload
    response = gfy_instance.check_status(key)
    while response != 'complete':
        time.sleep(30)
        response = gfy_instance.check_status(key)
        if response == 'encoding':
            continue
        elif response == 'NotFoundo':
            break
        elif response == 'error' or not response:
            break

    return response

def replytopost(submission, gfy_name):
    # does what it looks like it does
    url = 'https://www.gfycat.com/' + gfy_name
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
    # get lenght of the streamable and returns it
    r = requests.get(streamable_url)
    soup = BeautifulSoup(r.text,'lxml')

    html =  soup.find_all('script')
    #html_len = len(html) -4

    #streamable_len = html[html_len]['data-duration']

    for tag in html:
        try:
            streamable_len = tag['data-duration']
            break
        except KeyError:
            pass

    streamable_len = float(streamable_len)

    return streamable_len

def in_bad_list(sub_title):
    # checks to see if the title matches bad titles
    for title in bad_list:
        if title in sub_title.lower():
            print('streamable in do not comment list!')
            return True
        else:
            return False

def main():
    subreddits = ['hockey','pubattlegrounds']
    #subreddit = reddit.subreddit('hockey')
    old_ids = old_submission_ids()

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)

        try:

            for submission in subreddit.hot(limit=30):
                if re.search('streamable', submission.url) != None and submission.id not in old_ids and not in_bad_list(submission.title):
                    gfy_name = upload(submission.title, submission.url, submission.subreddit)

                    if check_status(gfy_name) == 'complete':
                        old_ids.append(submission.id)
                        replytopost(submission, gfy_name)

        except prawcore.exceptions.ServerError as e:
            print('error with praw, sleeping then restarting')
            time.sleep(10)
        except prawcore.exceptions.RequestException as e:
            print('request exception {}'.format(e))
            time.sleep(10)


reddit = praw_auth()
gfy_instance = gfy_auth()

if __name__ == '__main__':
    main()
