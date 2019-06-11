import keras
import numpy as np
import json
import re as regex
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
global graph,model
graph = tf.get_default_graph()
model=keras.models.load_model('sent_model1.h5')
# model._make_predict_function()

with open('vocab.json') as js:
    worddict=json.load(js)

def tokenize(tweet):
    def remove_by_regex(tweet,regexp):
        tweet=regex.sub(regexp,"",tweet)
        return tweet
    tweet = str(tweet.lower())
    tweet=remove_by_regex(tweet,regex.compile(r"http.?://[^\s]+[\s]?"))
    tweet=remove_by_regex(tweet,regex.compile(r"@[^\s]+[\s]?"))
    tweet=remove_by_regex(tweet,regex.compile(r"\s?[0-9]+\.?[0-9]*"))
    for remove in map(lambda r: regex.compile(regex.escape(r)), [",", ":", "\"", "=", "&", ";", "%", "$","@", "%", "^", "*", "(", ")", "{", "}","[", "]", "|", "/", "\\", ">", "<", "-","!", "?", ".","--", "---", "#"]):
        tweet=remove_by_regex(tweet,remove)
    return tweet

tokenizer = Tokenizer()
tokenizer.word_index=worddict

def sentiment(tweet):
    tweet=tokenize("".join(tweet))
    ntmp=tokenizer.texts_to_sequences([tweet])
    tmp_padded=pad_sequences([ntmp][0],maxlen=50)
    with graph.as_default():
        pre=model.predict(np.array([tmp_padded][0]))[0][0]
    return pre


#sentiment('you are ugly')




