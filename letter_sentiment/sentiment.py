from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as vaderSentiment


def get_sentiment(text_to_analyze):
    tb_sentiment = get_textblob_sentiment(text_to_analyze)
    v_sentiment = get_vadersentiment_sentiment(text_to_analyze)
    return [str.format('TextBlob: {0}', tb_sentiment), str.format('Vader: {0}', v_sentiment)]


def get_textblob_sentiment(text_to_analyze):
    text = TextBlob(text_to_analyze)
    sentiment = sentiment_to_string(text.sentiment.polarity)
    return str.format('{0} ({1:.3f})', sentiment, text.sentiment.polarity)


def get_vadersentiment_sentiment(text_to_analyze):
    analyzer = vaderSentiment()
    scores = analyzer.polarity_scores(text_to_analyze)
    neg = scores['neg']
    pos = scores['pos']
    polarity = pos - neg
    sentiment = sentiment_to_string(polarity)
    return str.format('{0} ({1:.3f})', sentiment, polarity)


def sentiment_to_string(polarity):
    if polarity <= -0.25:
        sentiment = 'negative'
    elif -0.25 < polarity < 0.25:
        sentiment = 'neutral'
    else:
        sentiment = 'positive'

    return sentiment



