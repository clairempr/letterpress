# elasticsearch stuff that's completely separate from any models
import json
import requests

from letters.es_settings import ES_ANALYZE, ES_MTERMVECTORS, ES_LETTER_URL, ES_SEARCH


def analyze_term(term, analyzer):
    query = json.dumps({
        "analyzer": analyzer,
        "text": term
    })

    result = do_es_analyze(query)
    if 'tokens' in result:
        analyzed_text = ' '.join(item['token'] for item in result['tokens'])
    else:
        analyzed_text = ''

    return analyzed_text


def get_mtermvectors(ids, fields):
    query = json.dumps({
        "ids": ids,
        "parameters": {
            "fields": fields,
            "offsets": "false",
            "positions": "false",
            "term_statistics": "false",
            "field_statistics": "false"
        }
    })

    return do_es_mtermvectors(query)


def get_sentiment_termvector_for_letter(letter_id):
    termvector = {}
    query = get_sentiment_termvector_query()

    result = do_es_termvectors_for_id(letter_id, query)
    if 'term_vectors' in result and 'contents' in result['term_vectors'] and 'terms' in result['term_vectors']['contents']:
        termvector = result['term_vectors']['contents']['terms']

    return termvector


def get_sentiment_termvector_for_text(text):
    termvector = {}

    query = json.dumps({
        "doc": {
            "contents": text
            },
        "fields": ["contents"],
        "per_field_analyzer": {
            "contents": "termvector_sentiment_analyzer"
            },
        "offsets": "true",
        "positions": "true",
        "term_statistics": "false",
        "field_statistics": "false",
    })

    result = do_es_termvectors_for_text(query)
    if 'term_vectors' in result and 'contents' in result['term_vectors'] and 'terms' in result['term_vectors']['contents']:
        termvector = result['term_vectors']['contents']['terms']

    return termvector


def get_sentiment_termvector_query():
    return json.dumps({
        "fields": ["contents"],
        "per_field_analyzer": {
            "contents": "termvector_sentiment_analyzer"
        },
        "offsets": "true",
        "positions": "false",
        "term_statistics": "false",
        "field_statistics": "false",
    })


def get_stored_fields_for_letter(letter_id, stored_fields):
    url = str.format('{0}{1}?stored_fields={2}', ES_LETTER_URL, str(letter_id), ','.join(stored_fields))
    response = requests.get(url)
    return json.loads(response.text)


def do_es_analyze(query):
    response = requests.get(ES_ANALYZE, data=query)
    return json.loads(response.text)


def do_es_mtermvectors(query):
    response = requests.get(ES_MTERMVECTORS, data=query)
    return json.loads(response.text)


def do_es_termvectors_for_id(id, query):
    termvectors_url = str.format('{0}{1}/_termvectors', ES_LETTER_URL, str(id))
    response = requests.get(termvectors_url, data=query)
    return json.loads(response.text)


def do_es_termvectors_for_text(query):
    termvectors_url = str.format('{0}_termvectors', ES_LETTER_URL)
    response = requests.get(termvectors_url, data=query)
    return json.loads(response.text)


def do_es_search(query):
    response = requests.get(ES_SEARCH, data=query)
    return json.loads(response.text)