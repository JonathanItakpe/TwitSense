__author__ = 'arathi'

import csv
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.svm import LinearSVC
from sklearn import cross_validation
from sklearn.metrics import classification_report
import numpy as np
from sklearn.metrics import accuracy_score
from classifier import processTweet
from nltk.corpus import stopwords
from sklearn.metrics import confusion_matrix, f1_score


# review.csv contains two columns
# first column is the review content (quoted)
# second column is the assigned sentiment (positive or negative)
def load_file():
    sentiment = []
    tweet = []

    with open('data/training.1600000.processed.noemoticon.csv', 'rb') as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        reader.next()

        for row in reader:
            # skip missing data
            if row[0] and row[5]:
                if row[0] == '0':
                    sentiment.append('negative')
                elif row[0] == '2':
                    sentiment.append('neutral')
                elif row[0] == '4':
                    sentiment.append('positive')
                tweet.append(processTweet(row[5]))

        return tweet, sentiment


def getStopWordList():
    # read the stopwords file and build a list
    punctuation = list(string.punctuation)
    stop = stopwords.words('english') + punctuation + ['AT_USER', 'URL', 'url', 'retweet', 'rt', 'at_user', 'RT']

    return stop


# preprocess creates the term frequency matrix for the review data set
def feature_selection():
    tweet, sentiment = load_file()
    count_vectorizer = HashingVectorizer(binary='true', decode_error='replace',
                                         stop_words=getStopWordList(), ngram_range=(1, 2))
    data = count_vectorizer.fit_transform(tweet)
    tfidf_data = TfidfTransformer(use_idf=False).fit_transform(data)

    return tfidf_data


def learn_model(data, target):
    # preparing data for split validation. 60% training, 40% test
    data_train, data_test, target_train, target_test = cross_validation.train_test_split(data, target, test_size=0.002,
                                                                                         random_state=43)
    classifier = LinearSVC().fit(data_train, target_train)
    predicted = classifier.predict(data_test)
    evaluate_model(target_test, predicted)


# read more about model evaluation metrics here
# http://scikit-learn.org/stable/modules/model_evaluation.html
def evaluate_model(target_true, target_predicted):
    confusion = np.array([[0, 0], [0, 0]])
    print classification_report(target_true, target_predicted)
    confusion += confusion_matrix(target_true, target_predicted)
    print 'Confusion Matrix:'
    print confusion
    print "The accuracy score is {:.2%}".format(accuracy_score(target_true, target_predicted))


def main():
    print 'reading file...'
    data, target = load_file()
    print 'vectorizing...'
    tf_idf = feature_selection()
    print 'training...'
    learn_model(tf_idf, target)


main()
