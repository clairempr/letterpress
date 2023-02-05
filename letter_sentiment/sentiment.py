from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as vaderSentiment


def get_sentiment(text_to_analyze):
    polarity = get_textblob_polarity(text_to_analyze)
    tb_sentiment = format_sentiment(sentiment_to_string(polarity), polarity)

    polarity = get_vadersentiment_polarity(text_to_analyze)
    v_sentiment = format_sentiment(sentiment_to_string(polarity), polarity)

    return [str.format('TextBlob: {0}', tb_sentiment), str.format('Vader: {0}', v_sentiment)]


def sentiment_to_string(polarity):
    if polarity < -0.5:
        sentiment = 'negative'
    elif polarity < -0.2:
        sentiment = 'slightly negative'
    elif polarity < 0.2:
        sentiment = 'neutral'
    elif polarity < 0.5:
        sentiment = 'slightly positive'
    else:
        sentiment = 'positive'

    return sentiment


def format_sentiment(sentiment, polarity):
    return str.format('{0} ({1:.3f})', sentiment, polarity)


def get_textblob_polarity(text_to_analyze):
    text = TextBlob(text_to_analyze)
    return text.sentiment.polarity


def get_vadersentiment_polarity(text_to_analyze):
    analyzer = vaderSentiment()
    scores = analyzer.polarity_scores(text_to_analyze)
    neg = scores['neg']
    pos = scores['pos']
    polarity = pos - neg
    return polarity


# surround sentences in text with styled <span>
def highlight_text_for_sentiment(text):
    # get highlights for both TextBlob sentiment and vaderSentiment
    highlighted_text_blob = ''
    highlighted_text_vader = ''

    blob = TextBlob(text)
    for sentence in blob.sentences:
        # TextBlob sentiment
        highlight = do_sentiment_highlight(sentence.string, sentence.polarity)
        highlighted_text_blob += highlight + ' '

        # vaderSentiment
        polarity = get_vadersentiment_polarity(sentence.string)
        highlight = do_sentiment_highlight(sentence.string, polarity)
        highlighted_text_vader += highlight + ' '

    return [highlighted_text_blob, highlighted_text_vader]


def do_sentiment_highlight(text, polarity):
    if polarity < -0.5:
        css_class = 'sentiment-highlight-neg'
    elif polarity < -0.2:
        css_class = 'sentiment-highlight-sorta-neg'
    elif polarity < 0.2:
        css_class = ''
    elif polarity < 0.5:
        css_class = 'sentiment-highlight-sorta-pos'
    else:
        css_class = 'sentiment-highlight-pos'

    if css_class:
        return str.format('<span class="{0}">{1}</span> <b>({2:.3f})</b> ',
                          css_class, text, polarity)
    else:
        return str.format('{0} <b>({1:.3f})</b> ',
                          text, polarity)
