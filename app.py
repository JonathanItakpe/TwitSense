from flask import Flask
from flask import render_template, flash, redirect, request, json
from classifiy_scikit import get_data
from bokeh.plotting import figure
import bokeh.plotting as plt
from bokeh.embed import components
from bokeh.charts import Bar, output_file, show, Histogram
import pandas as pd
from classifiy_scikit import getStopWordList
import nltk
from nltk import FreqDist

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/getResult', methods=['POST'])
def getresult():
    try:
        # RECEIVE DATA FROM INDEX WEB PAGE
        query = request.form['search']

        # GET TWEETS DATA FRAME BASED ON SEARCH QUERY
        data = get_data(query)

        # SELECT IMPORTANT COMPONENTS
        data = data[['tweetText', 'sentiment', 'weight', 'timeCreated']]

        # PLOT SENTIMENT BAR CHART
        data_sentiment = data['sentiment'].value_counts()

        # create a new plot with a title and axis labels
        p = Bar(data_sentiment, title='Tweets per Sentiment', width=400, height=400, xlabel='Sentiment', ylabel='Count')
        # output_file("histogram.html")
        # show(p)
        script_bar, div_bar = components(p)

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

        # SELECT TOP 10
        data = data.head(10)

        return render_template('result2.html', data=data.to_json(orient='records'), query=query, script_bar=script_bar,
                               div_bar=div_bar, freq=freq.to_json())
    except Exception as e:
        return render_template('error.html', error=e)


@app.route('/getAdvOptions', methods=['POST'])
def getmoreoptions():
    checked_url = False
    try:
        no_tweets = request.form['noTweets']
        name_clf = request.form['selClf']

        if 'url' in request.form:
            checked_url = True

        print no_tweets
        print name_clf
        print checked_url
    except Exception as e:
        print e
        return render_template('error.html', error=e)

if __name__ == '__main__':
    app.run(debug=True)
