# (elastic)search stuff that's specific to letters and related models
import collections
import json

from letter_sentiment.custom_sentiment import calculate_custom_sentiment
from letters import filter
from letters.elasticsearch import do_es_search, get_mtermvectors, get_stored_fields_for_letter, get_sentiment_termvector_for_letter
from letters.models import Letter


# Based on search criteria in request, query elasticsearch and
# return list of tuples containing letter and highlight
def do_letter_search(request, size, page_number):
    filter_values = filter.get_filter_values_from_request(request)
    search_text = filter_values.search_text

    if search_text:
        if '"' in search_text:
            contents_query = {'match_phrase': {'contents':
                                                   {'query': search_text, 'analyzer': 'standard'}}}
        else:
            contents_query = {'match': {'contents': {'query': search_text, 'fuzziness': 'AUTO'}}}
    else:
        contents_query = ''

    if page_number > 0:
        results_from = (page_number - 1) * size
    else:
        results_from = 0

    date_query = get_date_query(filter_values)
    filter_conditions = get_filter_conditions_for_query(filter_values)
    must_conditions = [condition for condition in [contents_query, date_query] if condition]

    query = json.dumps({
        'query': {
            'bool': {
                'must': must_conditions,
                'filter': filter_conditions
            }
        },
        'from': results_from,
        'size': size,
        'highlight': {
            'fields': {
                'contents': {'type': 'postings'}
            }
        },
        'stored_fields': ['contents.word_count'],
        'sort': {'date': {'order': 'asc'}}
    })

    results = do_es_search(query)
    search_results = []
    total = 0
    if 'hits' in results:
        total = results['hits']['total']
        for doc in results['hits']['hits']:
            letter = Letter.objects.get(pk=doc['_id'])
            highlight = get_doc_highlights(doc)
            word_count = get_doc_word_count(doc)
            sentiments = get_letter_sentiments(letter, word_count, filter_values.sentiment_ids)
            search_results.append((letter, highlight, sentiments))
    if total % size:
        pages = int(total / size + 1)
    else:
        pages = int(total / size)

    ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
    es_result = ES_Result(search_results=search_results, total=total, pages=pages)
    return es_result


def get_doc_highlights(doc):
    if 'highlight' in doc and 'contents' in doc['highlight']:
        return '<br>'.join(doc['highlight']['contents'])
    else:
        return ''


# sentiments is a list of (id, name/result)
def get_letter_sentiments(letter, word_count, sentiment_ids):
    if not sentiment_ids:
        return []

    sentiments = []
    termvector = get_sentiment_termvector_for_letter(letter.id)
    for sentiment_id in sentiment_ids:
        # Id 0 is used for standard sentiment,
        # since CustomSentiment starts numbering from 1
        # letter.sentiment() is an array while I'm experimenting with
        # different sentiment analysis packages
        if sentiment_id == 0:
            sentiments.append((sentiment_id, ' ,'.join(letter.sentiment())))
        else:
            custom_sentiment = calculate_custom_sentiment(sentiment_id, termvector, word_count)
            sentiments.append((sentiment_id, custom_sentiment))
    return sentiments


# get word_count from doc already returned from elasticsearch query
def get_doc_word_count(doc):
    if 'fields' in doc and 'contents.word_count' in doc['fields']:
        return doc['fields']['contents.word_count'][0]
    else:
        return 0


# get word_count for letter with letter_id using elasticsearch query
def get_letter_word_count(letter_id):
    stored_fields = ['contents.word_count']
    result = get_stored_fields_for_letter(letter_id, stored_fields)
    word_count = get_doc_word_count(result)
    return word_count


def get_multiple_word_frequencies(filter_values):
    words = filter_values.words
    contents_query = {'match': {'contents': ' '.join(words)}}
    filter_conditions = get_filter_conditions_for_query(filter_values)
    date_query = get_date_query(filter_values)
    must_conditions = [condition for condition in [contents_query, date_query] if condition]

    query = json.dumps({
        '_source': ['date'],
        'query': {
            'bool': {
                'must': must_conditions,
                'filter': filter_conditions
            }
        },
        'size': 10000,
    })

    es_result = do_es_search(query)

    if 'hits' in es_result and 'hits' in es_result['hits']:
        matching_docs = {hit['_id']: hit['_source']['date'] for hit in es_result['hits']['hits'] }
        ids = list(matching_docs.keys())
    else:
        matching_docs = {}
        ids = []

    mtermvectors = get_mtermvectors(ids, fields=['contents'])
    result = {}

    if 'docs' in mtermvectors:
        for mtvdoc in mtermvectors['docs']:
            id = mtvdoc['_id']
            year_month = get_year_and_month_from_date_string(matching_docs[id])
            if year_month not in result:
                result[year_month] = {word: 0 for word in words}
            terms = mtvdoc['term_vectors']['contents']['terms']
            for word in filter_values.words:
                # all words are indexed as lowercase, so look for lowercase version in termvector
                if word.lower() in terms:
                    result[year_month][word] += terms[word.lower()]['term_freq']

    return result


def get_year_and_month_from_date_string(date_string):
    components = date_string.split('-')
    return str.format('{year}-{month}',
                      year=components[0] if components else '0000',
                      month=components[1] if len(components) > 1 else '00')


def get_word_counts_per_month(filter_values):
    filter_conditions = get_filter_conditions_for_query(filter_values)
    date_query = get_date_query(filter_values)
    must_conditions = [condition for condition in [date_query] if condition]

    aggs = {
        "words_per_month": {
            "date_histogram": {
                "field": 'date',
                "interval": "month",
                "min_doc_count": 1,
            },
            "aggs": {
                "avg_words": {
                    "avg": {
                        "field": "contents.word_count"}
                },
                "total_words": {
                    "sum": {
                        "field": "contents.word_count"
                    }
                }
            }
        }
    }

    query = json.dumps({
        '_source': ['date'],
        'query': {
            'bool': {
                'must': must_conditions,
                'filter': filter_conditions
            }
        },
        'size': 10000,
        'sort': {'date': {'order': 'asc'}},
        'stored_fields': ['contents.word_count'],
        'aggs': aggs
    })

    es_result = do_es_search(query)
    word_counts = {}
    if 'aggregations' in es_result and 'words_per_month' in es_result['aggregations']:
        for bucket in es_result['aggregations']['words_per_month']['buckets']:
            year_month = bucket['key_as_string'][:7]
            word_counts[year_month] = {'avg_words': bucket['avg_words']['value'],
                                       'total_words': bucket['total_words']['value'],
                                       'doc_count': bucket['doc_count']}
    return word_counts


def get_date_query(filter_values):
    return {'range': {'date': {'gte': filter_values.start_date, 'lte': filter_values.end_date}}}


def get_filter_conditions_for_query(filter_values):
    filter_conditions = []
    source_ids = filter_values.source_ids
    writer_ids = filter_values.writer_ids
    if source_ids:
        filter_conditions.append({'terms': {'source': source_ids}})
    if writer_ids:
        filter_conditions.append({'terms': {'writer': writer_ids}})

    return filter_conditions




