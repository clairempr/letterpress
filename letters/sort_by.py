# Used for user-selected sort order
from letter_sentiment.custom_sentiment import get_custom_sentiments

DATE = 'DATE'
RELEVANCE = 'RELEVANCE'
SENTIMENT = 'SENTIMENT'


def get_selected_sentiment_id(filter_value):
    if not filter_value.startswith(SENTIMENT):
        return 0

    sentiment_id = int(filter_value.strip(SENTIMENT))
    return sentiment_id


def get_sentiments_for_sort_by_list():
    # Just sort by custom sentiment for now
    custom_sentiments = [(SENTIMENT + str(sentiment.id), sentiment.name) for sentiment in get_custom_sentiments()]
    return custom_sentiments
