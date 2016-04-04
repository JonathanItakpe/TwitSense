from flask import Flask, make_response
from flask import render_template, redirect, request, url_for, session, g, flash, Response, jsonify
from flask_oauth import OAuth
from bokeh.embed import components
from bokeh.charts import Bar
import pandas as pd
import json
import string, random
import numpy as np

from twitter_search import search_twitter
import classifier as act
from parse_config import parse_config
import os
import psycopg2

# setup flask
app = Flask(__name__)
app.config.from_object(__name__)
SECRET_KEY = os.urandom(20)
app.secret_key = SECRET_KEY
oauth = OAuth()
pd.set_option('display.max_colwidth', -1)

# Unicode Stringy Wahala!
# Ionno how this works but it fixes the ASCII error on Admin Page when reading from postgresql DB
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

# Get Consumer Keys
my_config = parse_config()

# Use Twitter as example remote application
twitter = oauth.remote_app('twitter',
                           # unless absolute urls are used to make requests, this will be added
                           # before all URLs.  This is also true for request_token_url and others.
                           base_url='https://api.twitter.com/1/',
                           # where flask should look for new request tokens
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           # where flask should exchange the token with the remote application
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           # twitter knows two authorizatiom URLs.  /authorize and /authenticate.
                           # they mostly work the same, but for sign on /authenticate is
                           # expected because this will give the user a slightly different
                           # user interface on the twitter side.
                           authorize_url='https://api.twitter.com/oauth/authenticate',
                           # the consumer keys from the twitter application registry.
                           consumer_key=my_config.get('consumer_key'),
                           consumer_secret=my_config.get('consumer_secret')
                           )


@twitter.tokengetter
def get_twitter_token():
    return session.get('twitter_token')


@app.route('/')
def index():
    session.pop('screen_name', None)
    try:
        if session['screen_name']:
            return render_template('index.html', pgtitle='Home')
    except KeyError:
        return render_template('login.html', pgtitle='Twitter Login')


@app.route('/loginTwitter')
def home():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    return render_template('index.html', pgtitle='Home')


@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
                                              next=request.args.get('next') or request.referrer or None))


@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return render_template('login.html')


@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    access_token = resp['oauth_token']
    session['access_token'] = access_token
    session['screen_name'] = resp['screen_name']
    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    return redirect(url_for('home'))


# noinspection PyPackageRequirements
@app.route('/getResult', methods=['POST'])
def getresult():
    checked_url = False
    try:
        # RECEIVE DATA FROM INDEX WEB PAGE
        if 'noTweets' in request.form:
            no_tweets = request.form['noTweets']
        else:
            checked_url = True  # Used to determine if i used the initial form or the advanced options
            no_tweets = 50

        if 'selClf' in request.form:
            name_clf = request.form['selClf']
        else:
            name_clf = 'Maximum Enthropy'

        if 'advQuery' in request.form:
            query = request.form['advQuery']
        else:
            query = request.form['search']

        if 'url' in request.form:
            checked_url = True

        # GET USER ACCESS KEYS
        token = session['twitter_token'][0]
        token_secret = session['twitter_token'][1]

        # GET TWEETS DATA FRAME BASED ON SEARCH QUERY
        # data = get_data(query, token=token, token_secret=token_secret)

        print 'Loading ' + name_clf + ' classifier...'
        clf = act.load_classifier(classifier=name_clf)
        print "Classifier completely loaded"

        print 'Connecting to Twitter...'
        print 'Getting ' + str(no_tweets) + ' tweets'
        twitter_result = search_twitter(query, no_tweets=no_tweets, token=token, token_secret=token_secret)
        print str(no_tweets) + 'Tweets Retrieved Successfully!'

        if checked_url:
            print 'Removing Tweets containing URL...'
            twitter_result = act.removeTweetsWithUrl(twitter_result)
            print 'Removed tweets containing URL'

        print 'Trying to create a Pandas DataFrame...'
        print 'Classifying Tweets...'
        data = act.toDataFrame(twitter_result, clf)
        print 'Tweets classified Correctly!'

        print 'Finishing up the DataSet'
        data = act.post_dataset(data)
        print 'DONE with dataset'

        script_bar, div_bar, all_data, piedata, freq, no_positive, no_negative = performComputation(data)

        top_10_tweets = get_top_tweets(all_data)

        resp = make_response(
            render_template('result.html', tot_tweets=no_tweets, no_positive=no_positive, no_negative=no_negative,
                            div_bar=div_bar, script_bar=script_bar, piedata=piedata, freq=freq, topTweets=top_10_tweets,
                            full_data=all_data, pd=pd))

        return resp
    except Exception as e:
        print e
        return render_template('error.html', error=e)


def performComputation(data):
    try:
        # SELECT IMPORTANT COMPONENTS
        data = data[['tweetText', 'sentiment', 'weight', 'timeCreated']]
        sentiment_valcounts = data['sentiment'].value_counts(sort=False)

        # PLOT SENTIMENT BAR CHART (BOKEH)
        # create a new plot with a title and axis labels
        p = Bar(sentiment_valcounts, title='Tweets per Sentiment', height=450,
                xlabel='Sentiment', ylabel='Count')
        print sentiment_valcounts
        # output_file("histogram.html")
        # show(p)
        script_bar, div_bar = components(p)
        # END OF BAR CHART

        # PIE/DONUT CHART (google api)
        s = sentiment_valcounts.to_frame()  # Convert series to dataframe
        sentiment_labels = list(s.index)  # Get the index [positive or negative]
        sentiment_values = [sentiment_valcounts[0], sentiment_valcounts[1]]

        piedata = [(sentiment_labels[0], np.asscalar(sentiment_valcounts[0])),
                   # Converting from numpy Int64 to normal int
                   (sentiment_labels[1],
                    np.asscalar(sentiment_valcounts[1]))]  # Converting from numpy Int64 to normal int

        no_positive_tweets = np.asscalar(sentiment_valcounts[0])
        no_negative_tweets = np.asscalar(sentiment_valcounts[1])

        # END PIE

        # WORDCLOUD
        # Get Stop Words
        stop = act.getStopWordList()

        text = data['tweetText']

        tokens = []

        for txt in text.values:
            tokens.extend([t.lower().strip(":,.") for t in txt.split()])

        filtered_tokens = [w for w in tokens if not w in stop]

        # freq_dist = FreqDist(filtered_tokens)

        p = pd.Series(filtered_tokens)

        # get the counts per word
        freq = p.value_counts()

        # How many max words do we want to give back
        freq = freq.ix[0:30]

        # print freq.keys()[:20]

        freq_json = freq.to_json()

        # response.headers.add('Access-Control-Allow-Origin', "*")
        # END OF WORDCLOUD

        return script_bar, div_bar, data, piedata, freq_json, no_positive_tweets, no_negative_tweets
    except Exception as e:
        print e
        return render_template('error.html', error=e)


@app.route('/_extend')
def extendsub():
    conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
    cursor = conn.cursor()

    txt_tweet = request.args.get('text', type=str)
    txt_sentiment = request.args.get('sentiment', type=str)

    query = "INSERT INTO public.extend_train (tweet_text, sentiment) VALUES (%s, %s);"
    data = (txt_tweet, txt_sentiment)

    cursor.execute(query, data)
    conn.commit()
    conn.close()

    result_ = 'Successfully Edited the Classification, changes will be effected within 24 hours!'

    return jsonify(result_text=result_)


# Getting Top tweets based on weight
def get_top_tweets(df):
    # Select Text and Weight
    df = df[['tweetText', 'weight']]
    df.sort_values('weight', ascending=False)
    df = pd.concat([df.head(5), df.tail(5)])
    return df


@app.route('/_classify')
def classify_tweet():
    text = request.args.get('text', 'God is good', type=str)
    clf = request.args.get('clf', 'Maximum Enthropy', type=str)
    classifier = act.load_classifier(clf)
    text = act.processTweet(text)
    text_sentiment = act.get_sentiment(text, classifier)
    return jsonify(sentiment=text_sentiment)


# ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN  ADMIN
@app.route('/adminStart')
def admin():
    try:
        if session['admin']:
            # Getting Extended Training set --- Created by user
            try:
                conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
            except:
                print "I am unable to connect to the database"

            cur = conn.cursor()

            cur.execute("""SELECT tweet_text, sentiment from extend_train""")

            rows = cur.fetchall()

            # Getting classifier Data
            try:
                conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
            except:
                print "I am unable to connect to the database"

            cur = conn.cursor()

            cur.execute("""SELECT clf_name, accuracy from classifier_table""")

            rows_clf = cur.fetchall()

            for row in rows_clf:
                if row[0] == 'Maximum Enthropy':
                    clf_max_nm = row[0]
                    clf_max_acc = row[1]
                elif row[0] == 'Naive Bayes':
                    clf_nb_nm = row[0]
                    clf_nb_acc = row[1]
                elif row[0] == 'Support Vector Machine':
                    clf_svm_nm = row[0]
                    clf_svm_acc = row[1]

            cur.execute("""Select count(*) from public.extend_train
                            UNION
                            Select count(*) from public.training_set;""")

            counts = cur.fetchall()
            res1 = 0
            for count in counts:
                res1 += count[0]  # Adds the result, 2 rows

            return render_template("admin.html", results=rows, clf_max_acc=clf_max_acc, clf_max_nm=clf_max_nm,
                                   clf_nb_acc=clf_nb_acc, clf_nb_nm=clf_nb_nm, clf_svm_acc=clf_svm_acc,
                                   clf_svm_nm=clf_svm_nm, tot_tweets_train=res1)
    except KeyError:
        return render_template('admin_login.html', pgtitle='Admin')


@app.route('/loginAdmin', methods=["POST"])
def loginAdmin():
    user = request.form['inputEmail']
    password = request.form['inputPassword']

    if user == 'jonathanitakpe@gmail.com' and password == 'C@ntH@ck':
        session['admin'] = user

        # Getting Extended Training set --- Created by user
        try:
            conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
        except:
            print "I am unable to connect to the database"

        cur = conn.cursor()

        cur.execute("""SELECT tweet_text, sentiment from extend_train""")

        rows = cur.fetchall()

        # Getting classifier Data
        try:
            conn = psycopg2.connect(database='twitsense', user='postgres', password='C@ntH@ck', host='localhost')
        except:
            print "I am unable to connect to the database"

        cur = conn.cursor()

        cur.execute("""SELECT clf_name, accuracy from classifier_table""")

        rows_clf = cur.fetchall()

        for row in rows_clf:
            if row[0] == 'Maximum Enthropy':
                clf_max_nm = row[0]
                clf_max_acc = row[1]
            elif row[0] == 'Naive Bayes':
                clf_nb_nm = row[0]
                clf_nb_acc = row[1]
            elif row[0] == 'Support Vector Machine':
                clf_svm_nm = row[0]
                clf_svm_acc = row[1]

        cur.execute("""Select count(*) from public.extend_train
                   UNION
                   Select count(*) from public.training_set;""")

        counts = cur.fetchall()
        res1 = 0
        for count in counts:
            res1 += count[0]  # Adds the result, 2 rows

        return render_template("admin.html", results=rows, clf_max_acc=clf_max_acc, clf_max_nm=clf_max_nm,
                               clf_nb_acc=clf_nb_acc, clf_nb_nm=clf_nb_nm, clf_svm_acc=clf_svm_acc,
                               clf_svm_nm=clf_svm_nm, tot_tweets_train=res1)
    else:
        return render_template("admin_login.html", pgtitle='Admin')


if __name__ == '__main__':
    app.run(debug=True)
