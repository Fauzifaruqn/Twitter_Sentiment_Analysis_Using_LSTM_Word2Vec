from flask import Flask, render_template,jsonify
# import keras
# model=keras.models.load_model('sent_model1.h5')
# model._make_predict_function()
import json
import sqlite3
import pandas as pd
import json
from collections import Counter
import string
import re
from cache import cache
import time
import pickle
# from twitter_stream import listener
from tweepy import OAuthHandler
from tweepy import Stream
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
os.chdir(os.path.realpath(os.path.dirname(__file__)))
from tweepy.streaming import StreamListener
from predict import sentiment
from unidecode import unidecode
import time
from threading import Lock, Timer
lock=Lock()
app = Flask(__name__)

POS_NEG_NEUT = 0.1
MAX_DF_LENGTH = 100
ckey="VGh88DmxoMy6wpc8wV6Ec10qG"
csecret="FK2Cm0jyFXu8vwUBdT4yBLG5oCDEqHug4AuPYOwdeNSj8e54EK"
atoken="953981441712508928-93uuwMBOjaYbzMRe4sD6DDLJD7gxLu5"
asecret="ZX523RnSih9cVyvRuqrFDpkpxJP5sqQ5EoITIExls0VYJ"
auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
streams=[]


def df_resample_sizes(df, maxlen=MAX_DF_LENGTH):
    df_len = len(df)
    resample_amt = 100
    vol_df = df.copy()
    vol_df['volume'] = 1

    ms_span = (df.index[-1] - df.index[0]).seconds * 1000
    rs = int(ms_span / maxlen)

    df = df.resample('{}ms'.format(int(rs))).mean()
    df.dropna(inplace=True)

    vol_df = vol_df.resample('{}ms'.format(int(rs))).sum()
    vol_df.dropna(inplace=True)

    df = df.join(vol_df['volume'])

    return df

def pos_neg_neutral(col):
    if col >= POS_NEG_NEUT:
        # positive
        return 1
    elif col <= -POS_NEG_NEUT:
        # negative:
        return -1

    else:
        return 0

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
        print(str(e))

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
                # print(data)
                return True
            if data['truncated']:
                tweet = unidecode(data['extended_tweet']['full_text'])
            else:
                tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            sent = sentiment(tweet)
            # print(time_ms, tweet, sent)
            with self.lock:
                self.data.append((time_ms, tweet, float(sent)))

        except KeyError as e:
            print(str("data ee"))
        return True

    def on_error(self, status):
        print("conn error")

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/graph')
def graph(chartID = 'chart_ID', chart_type = 'line', chart_height = 500):
    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height}
    # series = [{"name": 'Label1', "data": data['Y']}]
    title = {"text": 'My Title'}
    # xAxis = {"categories": data['X']}
    # yAxis = {"title": {"text": 'yAxis Label'}}
    return render_template('index.html', chartID=chartID, chart=chart,title=title)
 
@app.route('/static/data.json')
def getjson():
    conn = sqlite3.connect('twitter.db', check_same_thread=False)
    c=conn.cursor()
    n=c.execute("select count(*) from (select *  from sentiment ORDER BY id DESC, unix DESC LIMIT 100)  where sentiment < 0.5")
    neg=n.fetchone()[0]
    # t=c.execute("select count(*) from (select * from sentiment ORDER BY id DESC, unix DESC LIMIT 1000)")
    # tot=t.fetchone()[0]
    pos=100-neg
    df = pd.read_sql("SELECT * FROM sentiment ORDER BY id DESC, unix DESC LIMIT 1000", conn)
    # len(df)
    df.sort_values('unix', inplace=True)
    df['date'] = pd.to_datetime(df['unix'], unit='ms')
    df.set_index('date', inplace=True)
    init_length = len(df)
    df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df)/5)).mean()
    df = df_resample_sizes(df)
    X = df.index
    Y = df.sentiment_smoothed.values
    X=list(map(lambda x:str(x),X))
    Y2 = df.volume.values
    # print(len(X),len(Y))
    Y2=list(map(lambda x:int(x),Y2))
    d=[]
    for x in zip(X,Y):
        d.append(list(x))
    b=[]
    for y in zip(X,Y2):
        b.append(list(y))
    with open("./static/data.json", "w") as write_file:
        json.dump(d, write_file)
        print("Success")
    with open("./static/bar.json", "w") as write_file1:
        json.dump(b, write_file1)
    with open("./static/pie.json", "w") as write_file1:
        json.dump([['Positive',pos],["Negative",neg]], write_file1)
        
    return jsonify(d)       

@app.route('/static/bar.json')
def getvol():
    with open("./static/bar.json", "r") as read_file1:
        d=json.load(read_file1)
    return jsonify(d)

@app.route('/static/pie.json')
def getpie():
    with open("./static/pie.json", "r") as read_file2:
        p=json.load(read_file2)
    return jsonify(p)

@app.route('/table')
def table():
    con = sqlite3.connect('twitter.db', check_same_thread=False)
    df = pd.read_sql("SELECT * FROM sentiment ORDER BY id DESC, unix DESC LIMIT 5", con)
    df['date'] = pd.to_datetime(df['unix'], unit='ms')
    df = df.drop(['unix','id'], axis=1)
    df = df[['date','tweet','sentiment']]
    # print(df)
    date=df.date.values
    date=list(map(lambda x:str(x),date))
    tweet=df.tweet.values
    sent=df.sentiment.values
    s=[]
    for x in zip(date,tweet,sent):
        s.append(list(x))
    return render_template('table.html',s=s)

@app.route("/search/<key>")
def stream(key):
    create_table()
    try:
        for stream in streams:
            stream.disconnect()

        stream = Stream(auth, listener(lock))
        streams.append(stream)
        stream.filter(track=[str(key)])
        return "Success"
    except Exception as e:
        print(str(e))
    return "Success"


if __name__ == "__main__":
	app.run()

