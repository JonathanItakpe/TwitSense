# Import the necessary methods from tweepy library
import tweepy
import parse_config


tweet_loc = 'data/result.json'
parse_cfg = parse_config.parse_config()

config_my = parse_cfg


def search_twitter(keyword, no_tweets, token, token_secret):
    auth = tweepy.OAuthHandler(config_my.get('consumer_key'), config_my.get('consumer_secret'))
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    tweets = []
    for tweet in tweepy.Cursor(api.search,
                               q=keyword,
                               # count=no_tweets,
                               result_type="recent",
                               include_entities=True,
                               lang="en").items(no_tweets):
        # print tweet.text.replace('\n', ' ')
        tweets.append(tweet)
    # with open(tweet_loc, 'w') as f:
    #     for tweet in tweets:
    #         json.dump(tweet, f)
    #         f.write('\n')
    return tweets

if __name__ == '__main__':
    keyword = 'iPhone 6s'

