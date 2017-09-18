# elasticsearch stuff that's completely separate from any models
import json
import requests

from letters.es_settings import ES_CLIENT, ES_ANALYZE, ES_MTERMVECTORS, ES_LETTER_URL, ES_SEARCH
from letters.models import Letter


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
            "field_statistics": "false"
        }
    })

    return do_es_mtermvectors(query)


def get_sentiment_termvector_for_text(text):
    query = build_termvector_query(text=text, analyzer='termvector_sentiment_analyzer',
                                   offsets='true', positions='true')
    termvector = do_es_termvectors_for_text(query)
    return termvector


def build_termvector_query(text, analyzer, offsets, positions):
    query = {
        "fields": ["contents"],
        "per_field_analyzer": {
            "contents": analyzer
        },
        "offsets": offsets,
        "positions": positions,
        "field_statistics": "false",
    }

    # Add optional artificial document to query
    if text:
        query['doc'] = {
            "contents": text
        }

    return json.dumps(query)


def get_termvector_from_result(result):
    termvector = {}
    if 'term_vectors' in result \
            and 'contents' in result['term_vectors'] \
            and 'terms' in result['term_vectors']['contents']:
        termvector = result['term_vectors']['contents']['terms']

    return termvector


def get_stored_fields_for_letter(letter_id, stored_fields):
    url = str.format('{0}{1}?stored_fields={2}', ES_LETTER_URL,
                     str(letter_id), ','.join(stored_fields))
    response = requests.get(url)
    return json.loads(response.text)


def do_es_analyze(query):
    response = requests.get(ES_ANALYZE, data=query)
    return json.loads(response.text)


def do_es_mtermvectors(query):
    response = requests.get(ES_MTERMVECTORS, data=query)
    return json.loads(response.text)


def do_es_termvectors_for_text(query):
    termvectors_url = str.format('{0}_termvectors', ES_LETTER_URL)
    response = requests.get(termvectors_url, data=query)
    result = json.loads(response.text)
    return get_termvector_from_result(result)


def do_es_search(query):
    response = requests.get(ES_SEARCH, data=query)
    return json.loads(response.text)


# Temporarily index a document to use elasticsearch to calculate
# custom sentiment score for a piece of arbitrary text
def index_temp_document(text):
    ES_CLIENT.index(
        index=Letter._meta.es_index_name,
        doc_type=Letter._meta.es_type_name,
        id='temp',
        refresh=True,
        body={'contents': text}
    )


def delete_temp_document():
    ES_CLIENT.delete(
        index=Letter._meta.es_index_name,
        doc_type=Letter._meta.es_type_name,
        id='temp',
        refresh=True,
    )
