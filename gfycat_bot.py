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
import sqlite3
from logger import logger


###### Globals ######

bad_list = ['jay and dan']
config = configparser.ConfigParser(interpolation=None)
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')
dbtable = os.path.join(os.path.dirname(__file__), 'db/comments.db')

#### end Globals #####


class Connect(object):
    def __init__(self):
        self.conn = sqlite3.connect(dbtable)
        self.cur = self.conn.cursor()


class Search(object):
    table = 'comments'

    def __init__(self):
        self.db = Connect()

    def search(self,commentid):
        self.commentid = commentid
        cmd = "select commentid from {} where commentid = '{}'".format(self.table, commentid)
        try:
            self.db.cur.execute(cmd)
        except sqlite3.OperationalError as e:
            logger.error('error occured searching for comment id', extra={'error': e, 'commentid': commentid})
        result = self.db.cur.fetchone()
        if result is None:
            logger.info('commentid not found in db', extra={'commentid': commentid})
            return True
        elif result is not None:
            logger.info('commentid found in db', extra={'commentid': commentid})
            return False
        else:
            logger.error('something happened')

    def insert(self,value):
        value = value,
        cmd = 'INSERT into {} VALUES (?)'.format(self.table)
        try:
            self.db.cur.execute(cmd, value)
            self.db.conn.commit()
            logger.info('commentid commited', extra={'commentid': value[0]})
        except sqlite3.IntegrityError as e:
            logger.error('value already exists', extra={'error': e})
        except sqlite3.OperationalError as e:
            logger.error('error inserting comment', extra={'error': e})

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

    logger.info('Logged into PRAW')

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
    for comment in me.comments.new(limit=None):
        old_ids.append(comment.submission.id)

    logger.info('retrived old ids')

    return old_ids


def check_status(key):
    # check status of the upload
    retries = 0
    response = gfy_instance.check_status(key)
    while response != 'complete':
        time.sleep(30)
        response = gfy_instance.check_status(key)
        if response == 'encoding':
            if retries >= 10:
                logger.error('Encoding took over 5 minutes, exiting', extra={'gfyname': key})
                break
            else:
                retries += 1
                continue
        elif response == 'NotFoundo':
            break
        elif response == 'error' or not response:
            break

    return response


def get_comment_id(submission):
    if submission.comments[0].author == 'NHLConvertrRodriguez':
        return submission.comments[0]
    # first comment wasn't the right one, have to find it now
    else:
        try:
            for comment in submission.comments:
                if comment.author == 'NHLConvertrRodriguez':
                    return comment
        except AttributeError:
            logger.error('Could not find NHLConvertrRodriguez before having to load more comments')

    # if it winds up here then couldn't find the bot at all
    logger.info('ALT sticky not found, replying to thread')
    return submission.id


def replytopost(comment, gfy_name):
    # does what it looks like it does
    url = 'https://www.gfycat.com/' + gfy_name
    message = "[Gfycat Url]({})\n\n" \
                "***\n\n" \
                "^Why ^am ^I ^mirroring ^to ^gfycat? ^Because ^work ^blocks ^streamables".format(url)

    # while true loop for retries
    while True:
        try:
            comment.reply(message)
            logger.info('commented', extra={'gfyname': gfy_name, 'commentid': comment.id})
            break
        except praw.exceptions.APIException as e:
            logger.error('hit rate limit', extra={'error': e})
            time.sleep(60)
            continue
        except prawcore.exceptions.Forbidden as e: # probably banned if I get this
            logger.error('praw exception', extra={'error': e})
            break
        except:
            break


def streamable_length(streamable_url):
    # get length of the streamable and returns it
    r = requests.get(streamable_url)
    soup = BeautifulSoup(r.text,'lxml')

    html =  soup.find_all('script')
    #html_len = len(html) -4

    #streamable_len = html[html_len]['data-duration']

    for tag in html:
        try:
            streamable_len = tag['data-duration']
            break
        except KeyError as e:
            pass

    streamable_len = float(streamable_len)

    return streamable_len


def in_bad_list(sub_title):
    # checks to see if the title matches bad titles
    for title in bad_list:
        if title in sub_title.lower():
            logger.info('streamable in do not comment list!')
            return True
        else:
            return False


def main():
    subreddits = ['hockey','pubattlegrounds']
    old_comments = Search()

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)

        try:
            for submission in subreddit.new(limit=30):
                if re.search('streamable', submission.url) is not None and old_comments.search(submission.id) and not in_bad_list(submission.title):
                    gfy_name = upload(submission.title, submission.url, submission.subreddit)
                    # double posting sometimes, putting in db first to stop that
                    old_comments.insert(submission.id)

                    if check_status(gfy_name) == 'complete':
                        #old_comments.insert(submission.id)
                        comment = get_comment_id(submission)
                        replytopost(comment, gfy_name)
                    else:
                        logger.error('check_status returned not complete', extra={'gfyname': gfy_name})

        except prawcore.exceptions.ServerError as e:
            logger.error('error with praw, sleeping then restarting')
            time.sleep(10)
        except prawcore.exceptions.RequestException as e:
            logger.error('request exception', extra={'error': e})
            time.sleep(10)

    old_comments.db.conn.close()


reddit = praw_auth()
gfy_instance = gfy_auth()

if __name__ == '__main__':
    main()
