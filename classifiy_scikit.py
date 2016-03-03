import csv
import pandas as pd
from sklearn.externals import joblib
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
import re
from weights import get_weights
from twitter_search import search_twitter
from datetime import datetime
from nltk.corpus import stopwords
import string

pd.set_option('display.max_colwidth', -1)


def getStopWordList():
    # read the stopwords file and build a list
    stop = []
    punctuation = list(string.punctuation)
    stop = stopwords.words('english') + punctuation + ['AT_USER', 'URL', 'url', 'retweet', 'rt']
    return stop


def processTweet(tweet):
    # process the tweets

    # Convert to lower case
    tweet = tweet.lower()
    # Convert www.* or https?://* to URL ********
    tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet)
    # Convert @username to AT_USER ********
    tweet = re.sub('@[^\s]+', 'AT_USER', tweet)
    # Replace #word with word
    tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
    # Remove blank lines
    tweet = tweet.replace('\n', ' ')
    # trim
    tweet = tweet.strip('\'"')
    # Remove additional white spaces
    tweet = re.sub('[\s]+', ' ', tweet)
    return tweet


# Post process tweet to print
def postprocess(tweet):
    # Remove URLS
    tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', '', tweet)
    # Remove blank lines
    tweet = tweet.replace('\n', ' ')
    # trim
    tweet = tweet.strip('\'"')
    # Remove additional white spaces
    tweet = re.sub('[\s]+', ' ', tweet)
    return tweet


def get_sentiment(tweet, classifier):
    tweet = [tweet]
    sentiment = classifier.predict(tweet)[0]
    return sentiment


def evaluate_model(target_true, target_predicted):
    print classification_report(target_true, target_predicted)
    print "The accuracy score is {:.2%}".format(accuracy_score(target_true, target_predicted))


def gettimediff(time_):
    start = datetime.now()
    end = time_

    tdelta = start - end
    tdelta_secs = tdelta.total_seconds()

    if tdelta_secs <= 60:
        return str(int(tdelta_secs)) + ' Second(s)'
    elif 60 < tdelta_secs <= 3600:
        return str(int(tdelta_secs / 60)) + ' Minute(s)'
    elif 3600 < tdelta_secs <= 86400:
        return str(int(tdelta_secs / 3600)) + ' Hour(s)'
    else:
        return str(int(tdelta_secs / 86400)) + ' Day(s)'


def toDataFrame(tweets, clf):
    TweetDataSet = pd.DataFrame()

    TweetDataSet['timeCreated'] = [gettimediff(tweet.created_at) for tweet in tweets]
    TweetDataSet['tweetAcct'] = [tweet.user.screen_name for tweet in tweets]
    TweetDataSet['tweetText'] = [postprocess(tweet.text) for tweet in tweets]
    TweetDataSet['tweetRetweetCt'] = [tweet.retweet_count for tweet in tweets]
    TweetDataSet['tweetFavoriteCt'] = [tweet.favorite_count for tweet in tweets]
    TweetDataSet['verified'] = [tweet.user.verified for tweet in tweets]
    TweetDataSet['sentiment'] = [get_sentiment(processTweet(tweet.text), clf) for tweet in tweets]
    TweetDataSet['followerCount'] = [tweet.user.followers_count for tweet in tweets]
    return TweetDataSet


def get_data(keyword):
    startTime = datetime.now()
    # Pass the tweets list to the above function to create a DataFrame
    print 'Loading Naive Bayes Classifier...'
    clf = joblib.load('pickle/NB_Class_Vec.pkl')
    print '... 100% Loaded Completely!!! '
    print 'Retrieving tweets...'
    results = search_twitter(keyword)
    print type(results)
    print len(results)

    # REMOVE TWEETS THAT CONTAINS URL:
    regexp_url = re.compile('((www\.[^\s]+)|(https?://[^\s]+))')

    for result in results:
        if regexp_url.search(result.text) is not None:
            results.remove(result)
    # END OF REMOVAL

    DataSet = toDataFrame(results, clf)
    DataSet['weight'] = DataSet.apply(
            lambda x: get_weights(x['tweetRetweetCt'], x['tweetFavoriteCt'], x['sentiment'],
                                  x['verified'], x['followerCount']), axis=1)

    DataSet.drop_duplicates(subset='tweetText', keep='first', inplace=True)

    # DataSet['t'] = [element for element in DataSet['tweetText'].values if not element.startswith('RT')]

    # DataSet.drop_duplicates(subset='tweetAcct', keep=False, inplace=True)
    # DataSet.sort_values('tweetRetweetCt', ascending=False)

    print '\n ' + str(len(DataSet))
    print 'Total time taken to complete...' + str(datetime.now() - startTime)
    return DataSet


if __name__ == '__main__':
    get_data('Tesla Model S')
