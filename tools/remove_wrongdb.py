import os
import praw
import sqlite3
import configparser

config = configparser.ConfigParser(interpolation=None)
configfile = os.path.join(os.path.dirname(__file__), 'config.ini')
dbtable = os.path.join(os.path.dirname(__file__), 'comments.db')
conn = sqlite3.connect(dbtable)
cur = conn.cursor()


config.read(configfile)
reddit = praw.Reddit(client_id=config['praw']['client_id'],
             client_secret=config['praw']['client_secret'],
             user_agent='python:nourl:v0.01 by /u/BoxenOfDonuts',
             username=config['praw']['username'],
             password=config['praw']['password'])
print('logged into praw')

me = reddit.redditor('to_gfycat_bot')


def comment_id_generator():
    for comment in me.comments.new(limit=None):
        yield (comment.id,)

cur.executemany('delete from comments where commentid = (?)', comment_id_generator())

conn.commit()
conn.close()
