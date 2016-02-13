# Import the necessary methods from tweepy library
import tweepy
import parse_config


tweet_loc = 'data/result.json'
parse_cfg = parse_config.parse_config()

config_my = parse_cfg

auth = tweepy.OAuthHandler(config_my.get('consumer_key'), config_my.get('consumer_secret'))
auth.set_access_token(config_my.get('access_token'), config_my.get('access_token_secret'))
api = tweepy.API(auth)


def search_twitter(keyword):
    tweets = []
    for tweet in tweepy.Cursor(api.search,
                               q=keyword,
                               # count=page_count,
                               # rpp=100,
                               result_type="recent",
                               include_entities=True,
                               lang="en").items():
        # print tweet.text.replace('\n', ' ')
        tweets.append(tweet)

    # with open(tweet_loc, 'w') as f:
    #     for tweet in tweets:
    #         json.dump(tweet, f)
    #         f.write('\n')
    return tweets

if __name__ == '__main__':
    keyword = 'iPhone 6s'

