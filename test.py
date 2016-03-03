from bokeh.sampledata.autompg import autompg as df
from bokeh.charts import Bar, output_file, show
import pandas as pd
# GET TWEETS DATA FRAME BASED ON SEARCH QUERY
from classifier import get_data

data = get_data('Adidas')

# SELECT IMPORTANT COMPONENTS
data = data[['tweetText', 'sentiment', 'weight', 'timeCreated']]

# PLOT SENTIMENT BAR CHART
data2 = data['sentiment'].value_counts()

# create a new plot with a title and axis labels
p = Bar(data2, title='Tweets per Sentiment')
output_file("histogram.html")
show(p)
