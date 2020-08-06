import requests
import json, sys, os, string

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

def getReqJSON(url, args={}):
    """Generic function to get json from an api request"""
    if url.endswith('/'):
        url = url[:-1]

    arg_str = ""
    if isinstance(args, dict):
        if len(args) > 0:
            arg_str = '?' + '&'.join([str(k)+'='+str(args[k]) for k in args])
    elif not isinstance(args, list):
        args = [str(args)]
    
    if len(args) > 0 and isinstance(args, list):
        arg_str = '/' + '/'.join(args)
    
    url = url + arg_str
    r = requests.get(url=url)
    try:
        return r.json()
    except:
        try:
            return json.loads(r.text+'}') # why not lul (some apis used here need it)
        except:
            return None

def advice(id:int=-1):
    """Gets an encouraging piece of advice"""
    if id >= 0:
        resp = getReqJSON('https://api.adviceslip.com/advice/', id)
    else:
        resp = getReqJSON('https://api.adviceslip.com/advice/')

    if 'slip' in resp and 'id' in resp['slip'] and 'advice' in resp['slip']:
        return {'id': resp['slip']['id'], 'quote': resp['slip']['advice']}
    return {}

def dumbTrumpQuote(tag:str=""):
    """Gets a stupid trump quote"""
    if len(tag) > 0:
        # Sadly, the api has no way to get a quote by a specific tag. Lets just scan 16 random quotes to try and get a matching tag
        # Returns a random quote otherwise
        foundQuote = dumbTrumpQuote()
        for i in range(15):
            if 'tag' in foundQuote and tag.lower() in foundQuote['tag'].lower():
                break
            foundQuote = dumbTrumpQuote()
        return foundQuote
    
    # Get quote json and parse to dict safely
    resp = getReqJSON('http://tronalddump.io/random/quote')
    parsed = dict()
    if 'value' in resp:
        parsed['quote'] = resp['value']
    if 'appeared_at' in resp:
        parsed['date'] = str(resp['appeared_at']).replace('-',' ')[0:10]
    if 'tags' in resp and len(resp['tags']) > 0:
        parsed['tag'] = resp['tags'][0]
    if '_embedded' in resp and 'source' in resp['_embedded'] and len(resp['_embedded']['source']) > 0 and 'url' in resp['_embedded']['source'][0]:
        parsed['source'] = resp['_embedded']['source'][0]['url']
    return parsed


import nltk
from nltk.corpus import wordnet
nltk.download('vader_lexicon',quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()

from itertools import product
def get_max_sim(list1, list2):
    allsyns1 = set(ss for word in list1 for ss in wordnet.synsets(word))
    allsyns2 = set(ss for word in list2 for ss in wordnet.synsets(word))
    best = max((wordnet.wup_similarity(s1, s2) or 0, s1, s2) for s1, s2 in product(allsyns1, allsyns2))
    return best

def get_sentiment(phrase:str, useAbs=True, weighted=False, average=True):
    words = phrase.split(' ')

    max_len = max(words, key=lambda s: len(s))
    total_score = 0.0
    for w in words:
        score = sid.polarity_scores(w)['compound']
        if useAbs:
            score = abs(score)
        if weighted:
            score *= 1-(len(w)/max_len)
        total_score += score

    if average:
        total_score /= len(words)
    return total_score

def get_contradiction_score(phrase1:str,phrase2:str):
    return 1/(abs(get_sentiment(phrase1,average=False)-get_sentiment(phrase2,average=False))+abs(phrase1.count('not')-phrase2.count('not'))/2.0)

def get_trump_contradiction(sameTag=False):
    q1 = dumbTrumpQuote()
    if not 'tag' in q1 or not 'quote' in q1:
        return
    
    if sameTag:
        q2 = dumbTrumpQuote(tag=q1['tag'])
    else:
        q2 = dumbTrumpQuote()
    
    if not 'quote' in q2:
        return
    print('getting')
    return (get_contradiction_score(q1['quote'], q2['quote']), q1, q2)

if __name__ == "__main__":
    #print('Advice:\n'+str(advice()))
    #print('Stupid Trump Quote:\n'+str(dumbTrumpQuote()))
    #print('Stupid Trump Quote on Hillary:\n'+str(dumbTrumpQuote(tag='Hillary')))
    print(get_trump_contradiction())
