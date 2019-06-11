import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import sqlite3
from predict import sentiment
from unidecode import unidecode
import time
from threading import Lock, Timer
import pandas as pd


#consumer key, consumer secret, access token, access secret.
# https://apps.twitter.com/ to setup
# ckey="VGh88DmxoMy6wpc8wV6Ec10qG"
# csecret="FK2Cm0jyFXu8vwUBdT4yBLG5oCDEqHug4AuPYOwdeNSj8e54EK"
# atoken="953981441712508928-93uuwMBOjaYbzMRe4sD6DDLJD7gxLu5"
# asecret="ZX523RnSih9cVyvRuqrFDpkpxJP5sqQ5EoITIExls0VYJ"

# isolation lever disables automatic transactions,
# we are disabling thread check as we are creating connection here, but we'll be inserting from a separate thread (no need for serialization)
conn = sqlite3.connect('twitter.db', isolation_level=None, check_same_thread=False)
c = conn.cursor()

def create_table():
    try:
        c.execute("PRAGMA journal_mode=wal")
        c.execute("PRAGMA wal_checkpoint=TRUNCATE")
        c.execute("CREATE TABLE IF NOT EXISTS sentiment(id INTEGER PRIMARY KEY AUTOINCREMENT, unix INTEGER, tweet TEXT, sentiment REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS misc(key TEXT PRIMARY KEY, value TEXT)")
        c.execute("CREATE INDEX id_unix ON sentiment (id DESC, unix DESC)")
        c.execute("CREATE VIRTUAL TABLE sentiment_fts USING fts5(tweet, content=sentiment, content_rowid=id, prefix=1, prefix=2, prefix=3)")
        c.execute("""
            CREATE TRIGGER sentiment_insert AFTER INSERT ON sentiment BEGIN
                INSERT INTO sentiment_fts(rowid, tweet) VALUES (new.id, new.tweet);
            END
        """)
    except Exception as e:
        print(str("db error"))
create_table()
class listener(StreamListener):

    data = []
    lock = None
    def __init__(self, lock):
        self.lock = lock
        self.save_in_database()
        super().__init__()
    def save_in_database(self):
        Timer(1, self.save_in_database).start()
        with self.lock:
            if len(self.data):
                c.execute('BEGIN TRANSACTION')
                try:
                    c.executemany("INSERT INTO sentiment (unix, tweet, sentiment) VALUES (?, ?, ?)", self.data)
                except:
                    pass
                c.execute('COMMIT')

                self.data = []

    def on_data(self, data):
        try:
            data = json.loads(data)
            if 'truncated' not in data:
                print(data)
                return True
            if data['truncated']:
                tweet = unidecode(data['extended_tweet']['full_text'])
            else:
                tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            sent = sentiment(tweet)
            print(time_ms, tweet, sent)
            with self.lock:
                self.data.append((time_ms, tweet, float(sent)))

        except KeyError as e:
            print(str("data ee"))
        return True

    def on_error(self, status):
        print("conn error")
