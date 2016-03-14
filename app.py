from flask import Flask
from flask import render_template, redirect, request, url_for, session, g, flash
from flask_oauth import OAuth
from bokeh.embed import components
from bokeh.charts import Bar
import pandas as pd
from twitter_search import search_twitter
import classifier as act
from parse_config import parse_config
import os,time

# configuration
# SQLAlchemy database configuration. Here we are using postgresql
# database

SECRET_KEY = os.urandom(32)
# SECRET_KEY = 'damn-this-shit-sucks-bad'
DEBUG = True

# setup flask
app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()

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
            return render_template('index.html')
    except KeyError:
        return render_template('login.html')


@app.route('/loginTwitter')
def home():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    return render_template('index.html')


@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
                                              next=request.args.get('next') or request.referrer or None))


@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('index'))


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


@app.route('/getResult', methods=['POST'])
def getresult():
    checked_url = False
    try:

        # RECEIVE DATA FROM INDEX WEB PAGE
        if 'noTweets' in request.form:
            no_tweets = request.form['noTweets']
        else:
            no_tweets = 300

        if 'selClf' in request.form:
            name_clf = request.form['selClf']
        else:
            name_clf = 'Naive Bayes'

        if 'advQuery' in request.form:
            query = request.form['advQuery']
        else:
            query = request.form['search']

        if 'url' in request.form:
            checked_url = True

        # VERIFY RESULT
        print query
        print str(no_tweets)
        print name_clf
        print str(checked_url)
        # GET USER ACCESS KEYS
        token = session['twitter_token'][0]
        token_secret = session['twitter_token'][1]

        # GET TWEETS DATA FRAME BASED ON SEARCH QUERY
        # data = get_data(query, token=token, token_secret=token_secret)

        print 'Loading ' + name_clf + ' classifier...'
        clf = act.load_classifier(classifier=name_clf)
        print 'Classifier completely loaded'

        print 'Connecting to Twitter...'
        print 'Getting ' + str(no_tweets) + ' tweets'
        twitter_result = search_twitter(query, no_tweets=no_tweets, token=token, token_secret=token_secret)
        print str(no_tweets) + 'Tweets Retrieved Successfully!'

        if checked_url==True:
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

        top10, script_bar, div_bar, all_data = performComputation(data)

        return render_template('result2.html', data=top10.to_json(orient='records'), query=query, script_bar=script_bar,
                               div_bar=div_bar, full_data=all_data)
    except Exception as e:
        print e
        return render_template('error.html', error=e)


def performComputation(data):
    try:
        # SELECT IMPORTANT COMPONENTS
        data = data[['tweetText', 'sentiment', 'weight', 'timeCreated']]

        # PLOT SENTIMENT BAR CHART
        # create a new plot with a title and axis labels
        p = Bar(data['sentiment'].value_counts(), title='Tweets per Sentiment', width=400, height=400,
                xlabel='Sentiment', ylabel='Count')
        # output_file("histogram.html")
        # show(p)
        script_bar, div_bar = components(p)
        # END OF BAR CHART
        '''
        # WORDCLOUD
        # Get Stop Words
        stop = getStopWordList()

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
        freq = freq.ix[0:50]

        print freq.keys()[:20]
        # END OF WORDCLOUD
        '''
        # SELECT TOP 10 TWEETS
        data_tweets = data.head(10)

        return data_tweets, script_bar, div_bar, data
    except Exception as e:
        print e
        return render_template('error.html', error=e)


if __name__ == '__main__':
    app.run(debug=True)
