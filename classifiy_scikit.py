import csv
import pandas as pd
from sklearn.externals import joblib
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
import re
from weights import get_weights
from twitter_search import search_twitter
from datetime import datetime

pd.set_option('display.max_colwidth', -1)

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


# start replaceTwoOrMore
def replaceTwoOrMore(s):
    # look for 2 or more repetitions of character and replace with the character itself
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1\1", s)


def load_file(clf):
    # inpTweets = csv.reader(open('data/training.1600000.processed.noemoticon.csv', 'rb'), delimiter=',')
    tweets = []
    sentiment = []
    with open('data/testdata.manual.2009.06.14.csv', 'rb') as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        reader.next()
        for row in reader:
            tweets.append(row[5])
            sentiment.append(get_sentiment(row[5], clf))
    return tweets


def get_sentiment(tweet, classifier):
    tweet = [tweet]
    sentiment = classifier.predict(tweet)[0]
    return sentiment


def evaluate_model(target_true, target_predicted):
    print classification_report(target_true, target_predicted)
    print "The accuracy score is {:.2%}".format(accuracy_score(target_true, target_predicted))


def toDataFrame(tweets, clf):
    TweetDataSet = pd.DataFrame()

    TweetDataSet['tweetText'] = [tweet.text for tweet in tweets]
    TweetDataSet['tweetRetweetCt'] = [tweet.retweet_count for tweet in tweets]
    TweetDataSet['tweetFavoriteCt'] = [tweet.favorite_count for tweet in tweets]
    TweetDataSet['verified'] = [tweet.user.verified for tweet in tweets]
    TweetDataSet['sentiment'] = [get_sentiment(processTweet(tweet.text), clf) for tweet in tweets]
    TweetDataSet['followerCount'] = [tweet.user.followers_count for tweet in tweets]
    # TweetDataSet['weight'] = [get_weights(tweet.retweet_count, tweet.favorite_count,
    #                                       get_sentiment(processTweet(tweet.text), clf),
    #                                       tweet.user.verified, tweet.user.followers_count) for tweet in tweets]

    return TweetDataSet


def get_data(keyword):
    startTime = datetime.now()
    # Pass the tweets list to the above function to create a DataFrame
    print 'Loading Naive Bayes Classifier...'
    clf = joblib.load('pickle/NB_Class_Vec.pkl')
    print '... 100% Loaded Completely!!! '

    print 'Retrieving tweets...'
    results = search_twitter(keyword, 10)
    DataSet = toDataFrame(results, clf)
    DataSet['weight'] = DataSet.apply(
            lambda x: get_weights(x['tweetRetweetCt'], x['tweetFavoriteCt'], x['sentiment'],
                                  x['verified'], x['followerCount']), axis=1)
    # print 'Total time taken to complete...' + str(datetime.now() - startTime)
    return DataSet
