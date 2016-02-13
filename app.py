from flask import Flask
from flask import render_template, flash, redirect, request, json
from classifiy_scikit import get_data
from bokeh.plotting import figure
from bokeh.embed import components
app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/getResult', methods=['POST'])
def getresult():
    try:
        query = request.form['search']
        data = get_data(query)
        data = data[['tweetText', 'sentiment', 'weight', 'timeCreated']]
        # data = data.to_json()
        data = data.head(10)
        return render_template('result2.html', data=data.to_json(orient='records'), query=query)
    except Exception as e:
        return render_template('error.html', error=e)


if __name__ == '__main__':
    app.run(debug=True)
