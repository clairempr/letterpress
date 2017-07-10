import collections
from letters.models import Letter
from letter_sentiment.custom_sentiment import get_custom_sentiments

# when words not filled in stats request, give some stats for these:
DEFAULT_STATS_SEARCH_WORDS = ['&', 'and']


# get list of writers, dates, etc to fill filter fields in page
def get_initial_filter_values():
    sources = sorted({letter.source for letter in Letter.objects.all()})
    writers = sorted({letter.writer for letter in Letter.objects.all()})
    dates = sorted({letter.index_date() for letter in Letter.objects.all()})
    sentiments = get_sentiment_list()

    if dates:
        start_date = dates[0]
        end_date = dates[-1]
    else:
        start_date = ''
        end_date = ''

    return {'sources': sources, 'writers': writers, 'start_date': start_date, 'end_date': end_date,
            'words': DEFAULT_STATS_SEARCH_WORDS, 'sentiments': sentiments}


# Return list of sentiments, both standard and custom, in named tuple with id and name
def get_sentiment_list():
    Sentiment = collections.namedtuple('Sentiment', ['id', 'name'])
    sentiments = [Sentiment(id=0, name='Positive/negative')]
    custom_sentiments = [Sentiment(id=sentiment.id, name=sentiment.name) for sentiment in get_custom_sentiments()]
    sentiments.extend(custom_sentiments)
    return sentiments


# Get filter values entered by user
def get_filter_values_from_request(request):
    search_text = request.POST.get('search_text')
    # Ajax request
    if request.is_ajax():
        source_ids = request.POST.getlist('sources[]')
        writer_ids = request.POST.getlist('writers[]')
        words = request.POST.getlist('words[]')
        sentiment_ids = request.POST.getlist('sentiments[]')
    else:
        source_ids = request.POST.getlist('source')
        writer_ids = request.POST.getlist('writer')
        words = []  # Ajax only
        sentiment_ids = []  # Ajax only

    # source and writer ids need to be ints for Elasticsearch
    source_ids = [int(id) for id in source_ids]
    writer_ids = [int(id) for id in writer_ids]

    start_date = get_start_date_from_request(request)
    end_date = get_end_date_from_request(request)

    sentiment_ids = [int(id) for id in sentiment_ids]
    sort_by = request.POST.get('sort_by')

    FilterValues = collections.namedtuple('FilterValues',
        ['search_text', 'source_ids', 'writer_ids', 'start_date', 'end_date', 'words',
         'sentiment_ids', 'sort_by'])
    filter_values = FilterValues(
        search_text=search_text,
        source_ids=source_ids,
        writer_ids=writer_ids,
        start_date=start_date,
        end_date=end_date,
        words=words,
        sentiment_ids=sentiment_ids,
        sort_by=sort_by
    )
    return filter_values


def get_start_date_from_request(request):
    start_date_value = request.POST.get('start_date') if request.POST.get('start_date') else '0001-01-01'
    return start_date_value


def get_end_date_from_request(request):
    end_date_value = request.POST.get('end_date') if request.POST.get('end_date') else '9999-12-31'
    return end_date_value


def display_date_to_sort_date(display_date):
    date_parts = display_date.split('-')
    return str.format('{:0>4}{:0>2}{:0>2}', date_parts[0], date_parts[1], date_parts[2])
