import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
import string
import pickle
from nltk.corpus import stopwords
from sklearn.externals import joblib
from classifiy_scikit import processTweet

def create_tfidf(f):
    sentiment = []
    tweet = []

    with open(f, 'rb') as csv_file:
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
                tweet.append(processTweet(row[5]))  # .decode('latin-1').encode('utf-8'))

    return tweet, sentiment


def getStopWordList():
    # read the stopwords file and build a list
    punctuation = list(string.punctuation)
    stop = stopwords.words('english') + punctuation + ['AT_USER', 'URL', 'url', 'retweet', 'rt']

    return stop


def vectorize(tweet, sentiment):
    count_vectorizer = TfidfVectorizer(analyzer='word', binary='true', stop_words=getStopWordList(),
                                       decode_error='replace',
                                       ngram_range=(1, 2), use_idf=False)
    tweet = count_vectorizer.fit_transform(tweet)
    print 'DONE with vectorize'
    print tweet.shape
    return tweet


def evaluate_model(target_true, target_predicted):
    print classification_report(target_true, target_predicted)
    print "The accuracy score is {:.2%}".format(accuracy_score(target_true, target_predicted))


if __name__ == '__main__':
    print 'Reading and pre processing data...'
    tweet, sentiment = create_tfidf('data/training.1600000.processed.noemoticon.csv')

    print 'Vectorizing in process...'
    tf = HashingVectorizer(analyzer='word', binary='true', stop_words=getStopWordList(), decode_error='replace',
                           ngram_range=(1, 2))

    clf = LinearSVC()

    print 'pipelining...'
    vec_clf = Pipeline([('tfvec', tf), ('svm', clf)])

    print 'fitting...'
    vec_clf.fit(tweet, sentiment)

    print 'Dumping to file...'
    _ = joblib.dump(vec_clf, 'pickle/SVM.pkl', compress=9)

    # tweet_vec = vectorize(tweet, sentiment)
    # learn_model(tweet_vec, sentiment)
