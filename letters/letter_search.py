""" (elastic)search stuff that's specific to letters and related models """
import collections
import json

from letters import filter as letters_filter
from letters.elasticsearch import do_es_search, get_mtermvectors, get_stored_fields_for_letter
from letters.models import Letter
from letters.sort_by import DATE, SENTIMENT, get_selected_sentiment_id
from letter_sentiment.custom_sentiment import get_custom_sentiment_for_letter, \
    get_custom_sentiment_name
from letter_sentiment.elasticsearch import get_sentiment_function_score_query, \
    get_sentiment_match_query
from letter_sentiment.sentiment import format_sentiment


def do_letter_search(request, size, page_number):
    """
    Based on search criteria in request, query elasticsearch and
    return list of tuples containing letter and highlight
    """

    filter_values = letters_filter.get_filter_values_from_request(request)

    if page_number > 0:
        results_from = (page_number - 1) * size
    else:
        results_from = 0

    if filter_values.sort_by and filter_values.sort_by.startswith(SENTIMENT):
        sentiment_id = get_selected_sentiment_id(filter_values.sort_by)
        sentiment_match_query = get_sentiment_match_query(sentiment_id)
        custom_sentiment_name = get_custom_sentiment_name(sentiment_id)
    else:
        sentiment_match_query = []
        sentiment_id = 0

    # when sorting by custom sentiment, wrap the bool query in a function_score query
    bool_query = {
        'should': sentiment_match_query,
        'filter': get_filter_conditions_for_query(filter_values)
    }

    letter_match_query = get_letter_match_query(filter_values)
    if letter_match_query:
        bool_query['must'] = letter_match_query

    if sentiment_match_query:
        query = {
            'function_score': get_sentiment_function_score_query(bool_query)
        }
    else:
        query = {
            'bool': bool_query
        }

    query_json = {
        'query': query,
        'from': results_from,
        'size': size,
        'highlight': get_highlight_options(filter_values),
        'stored_fields': ['contents.word_count'],
        'sort': [get_sort_conditions(filter_values.sort_by)]
    }

    results = do_es_search(index=[Letter._meta.es_index_name], query=json.dumps(query_json))
    search_results = []
    total = 0
    if 'hits' in results:
        total = results['hits']['total']
        for doc in results['hits']['hits']:
            letter = Letter.objects.get(pk=doc['_id'])
            # Only show Elasticsearch higlights if user explicitly searched for a term
            # Don't show highlights associated with custom sentiment search terms
            highlight = get_doc_highlights(doc) if letter_match_query else ''
            score = doc['_score']
            if sentiment_id:
                sentiments = get_letter_sentiments(letter,
                                                   [id for id in filter_values.sentiment_ids if id != sentiment_id])
                sentiments.append((sentiment_id, format_sentiment(custom_sentiment_name, score)))
            else:
                sentiments = get_letter_sentiments(letter, filter_values.sentiment_ids)

            search_results.append((letter, highlight, sentiments, score))
    if total % size:
        pages = int(total / size + 1)
    else:
        pages = int(total / size)

    ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
    es_result = ES_Result(search_results=search_results, total=total, pages=pages)
    return es_result


def get_doc_highlights(doc):
    """
    Return a <br>-separated list of Elasticsearch highlights
    """

    if 'highlight' in doc:
        if 'contents' in doc['highlight']:
            return '<br>'.join(doc['highlight']['contents'])
        elif 'contents.custom_sentiment' in doc['highlight']:
            return '<br>'.join(doc['highlight']['contents.custom_sentiment'])

    return ''


def get_letter_sentiments(letter, sentiment_ids):
    """
    Return a list of (id, name/result) consisting of sentiments with sentiment_ids
    for letter
    """

    if not sentiment_ids:
        return []

    sentiments = []
    for sentiment_id in sentiment_ids:
        sentiment_id = int(sentiment_id)
        # Id 0 is used for standard sentiment,
        # since CustomSentiment starts numbering from 1
        # letter.sentiment() is an array while I'm experimenting with
        # different sentiment analysis packages
        if sentiment_id == 0:
            letter_sentiments = letter.sentiment()
            sentiments.append((sentiment_id, letter_sentiments))
        else:
            custom_sentiment = get_custom_sentiment_for_letter(letter.id, sentiment_id)
            sentiments.append((sentiment_id, custom_sentiment))
    return sentiments


def get_doc_word_count(doc):
    """
    Get word_count from doc already returned from Elasticsearch query
    """

    if 'fields' in doc and 'contents.word_count' in doc['fields']:
        return doc['fields']['contents.word_count'][0]

    return 0


def get_letter_word_count(letter_id):
    """
    Get word_count for letter with letter_id using Elasticsearch query
    """

    stored_fields = ['contents.word_count']
    result = get_stored_fields_for_letter(letter_id, stored_fields)
    word_count = get_doc_word_count(result)
    return word_count


def get_multiple_word_frequencies(filter_values):
    """
    Get term frequencies for mtermvectors returned by Elasticsearch using the given filters
    """

    words = filter_values.words
    query = json.dumps({
        '_source': ['date'],
        'query': {
            'bool': {
                'must': {'match': {'contents': ' '.join(words)}},
                'filter': get_filter_conditions_for_query(filter_values)
            }
        },
        'size': 10000,
    })

    es_result = do_es_search(index=[Letter._meta.es_index_name], query=query)

    if 'hits' in es_result and 'hits' in es_result['hits']:
        matching_docs = {hit['_id']: hit['_source']['date'] for hit in es_result['hits']['hits']}
        ids = list(matching_docs.keys())
    else:
        matching_docs = {}
        ids = []

    mtermvectors = get_mtermvectors(ids, fields=['contents'])
    result = {}

    if 'docs' in mtermvectors:
        for mtvdoc in mtermvectors['docs']:
            doc_id = mtvdoc['_id']
            year_month = get_year_month_from_date(matching_docs[doc_id])
            if year_month not in result:
                result[year_month] = {word: 0 for word in words}
            terms = mtvdoc['term_vectors']['contents']['terms']
            for word in filter_values.words:
                # all words are indexed as lowercase, so look for lowercase version in termvector
                if word.lower() in terms:
                    result[year_month][word] += terms[word.lower()]['term_freq']

    return result


def get_year_month_from_date(date_string):
    """
    Extract year/month/day from date_string and return YYYY-MM formatted date,
    with '0000' for year if date_string empty and '00' for month if none in date_string
    """

    components = date_string.split('-')
    return str.format('{year}-{month}',
                      year=components[0] if components and components[0] else '0000',
                      month=components[1] if len(components) > 1 else '00')


def get_word_counts_per_month(filter_values):
    """
    Use Elasticsearch query with aggregations to retrieve counts in letters written in a given month
    for words given in filter_values, and return them
    """

    filter_conditions = get_filter_conditions_for_query(filter_values)

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
                'filter': filter_conditions
            }
        },
        'size': 10000,
        'sort': {'date': {'order': 'asc'}},
        'stored_fields': ['contents.word_count'],
        'aggs': aggs
    })

    es_result = do_es_search(index=[Letter._meta.es_index_name], query=query)
    word_counts = {}
    if 'aggregations' in es_result and 'words_per_month' in es_result['aggregations']:
        for bucket in es_result['aggregations']['words_per_month']['buckets']:
            year_month = bucket['key_as_string'][:7]
            word_counts[year_month] = {'avg_words': bucket['avg_words']['value'],
                                       'total_words': bucket['total_words']['value'],
                                       'doc_count': bucket['doc_count']}
    return word_counts


def get_letter_match_query(filter_values):
    """
    Take search_text from filter_values and return a query for contents
    """

    contents_query = ''
    search_text = filter_values.search_text
    if search_text:
        # If search_text contains quotes, an entire phrase needs to be matched
        if '"' in search_text:
            contents_query = {'match_phrase': {'contents':
                                                   {'query': search_text, 'analyzer': 'standard'}}}
        else:
            contents_query = {'match': {'contents': {'query': search_text, 'fuzziness': 'AUTO'}}}

    return contents_query


def get_date_query(filter_values):
    """
    Return date query for Elasticsearch based on date range in filter_values
    """

    return {'range': {'date': {'gte': filter_values.start_date, 'lte': filter_values.end_date}}}


def get_filter_conditions_for_query(filter_values):
    """
    Get a date_query for Elasticsearch based on filter_values,
    and add 'terms' with source_ids and writer_ids if they're present in filter_values
    """

    filter_conditions = [get_date_query(filter_values)]
    source_ids = filter_values.source_ids
    writer_ids = filter_values.writer_ids
    if source_ids:
        filter_conditions.append({'terms': {'source': source_ids}})
    if writer_ids:
        filter_conditions.append({'terms': {'writer': writer_ids}})

    return filter_conditions


def get_highlight_options(filter_values):
    """
    Return something something to do with highlighting for an Elasticsearch query,
    depending on whether it's a custom sentiment
    """

    if filter_values.sort_by and filter_values.sort_by.startswith(SENTIMENT):
        return {
            # 'tags_schema': 'styled',
            'pre_tags': ['<span class="hlt1">', '<span class="hlt2">'],
            'post_tags': ['</span>', '</span>'],
            'fields': {
                'contents.custom_sentiment':
                    {'type': 'fvh', 'number_of_fragments': 0, 'phrase_limit': 500}
            }
        }

    return {
        'fields': {
            'contents': {'type': 'postings', 'number_of_fragments': 6}
        }
    }


def get_sort_conditions(sort_by):
    """
    Return field/order to use for sorting in Elasticsearch query,
    depending on type of sorting
    """

    if sort_by == DATE or sort_by == '':
        sort_field = 'date'
        sort_order = 'asc'

    else:  # RELEVANCE or SENTIMENT
        return '_score'

    return {sort_field: {'order': sort_order}}
