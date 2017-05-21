import collections
import json
import requests
from letters.models import Letter
from letters import filter
from letters import es_settings


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
        'sort': {'date': {'order': 'asc'}}
    })

    results = do_es_search(query)
    search_results = []
    total = 0
    if 'hits' in results:
        total = results['hits']['total']
        for doc in results['hits']['hits']:
            letter = Letter.objects.get(pk=doc['_id'])
            highlight = ''
            if 'highlight' in doc and 'contents' in doc['highlight']:
                highlight = '<br>'.join(doc['highlight']['contents'])
            search_results.append((letter, highlight))
    if total % size:
        pages = int(total / size + 1)
    else:
        pages = int(total / size)

    ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
    es_result = ES_Result(search_results=search_results, total=total, pages=pages)
    return es_result


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

    mtermvectors = get_mtermvectors(ids)
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


def get_mtermvectors(ids):
    query = json.dumps({
        "ids": ids,
        "parameters": {
            "fields": ["contents"],
            "offsets": "false",
            "positions": "false",
            "term_statistics": "false",
            "field_statistics": "false"
        }
    })

    return do_es_mtermvectors(query)


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


def do_es_mtermvectors(query):
    response = requests.get(es_settings.ES_MTERMVECTORS, data=query)
    results = json.loads(response.text)
    return results


def do_es_search(query):
    response = requests.get(es_settings.ES_SEARCH, data=query)
    results = json.loads(response.text)
    return results

