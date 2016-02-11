
def get_weights(retweets, favs, sentiment, verified, follow_count):
    weight = 10

    if sentiment == 'negative':
        weight *= -1

    if verified == 'False' and follow_count >= 5000:
        weight *= 0.95
    elif verified == 'False' and follow_count <= 5000:
        weight *= 0.9

    if retweets >= 1:
        if retweets <= 10:
            weight *= 0.8
    elif retweets > 10:
        weight *= 0.9
    elif retweets == 0:
        weight *= 0.5

    if favs >= 1:
        if favs <= 5:
            weight *= 0.9
    elif favs > 10:
        weight *= 0.95
    elif favs == 0:
        weight *= 0.85

    return weight
