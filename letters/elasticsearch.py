# elasticsearch stuff that's completely separate from any models
import elasticsearch
import json
import requests

from letters.es_settings import ES_CLIENT, ES_LETTER_URL
from letters.models import Letter
from letterpress.exceptions import ElasticsearchException


def analyze_term(term, analyzer):
    """
    Builds a query using analyzer and term, call do_es_analyze(query),
    and return the analyzed text if there are tokens in the result, otherwise it returns an empty string
    """

    query = json.dumps({
        "analyzer": analyzer,
        "text": term
    })

    result = do_es_analyze(index=Letter._meta.es_index_name, query=query)
    if 'tokens' in result:
        analyzed_text = ' '.join(item['token'] for item in result['tokens'])
    else:
        analyzed_text = ''

    return analyzed_text


def get_mtermvectors(ids, fields):
    """
    Build an Elasticsearch query, using ids and fields,
    call do_es_mtermvectors(query), and return its return value
    """
    query = json.dumps({
        "ids": ids,
        "parameters": {
            "fields": fields,
            "offsets": "false",
            "positions": "false",
            "field_statistics": "false"
        }
    })

    return do_es_mtermvectors(index=Letter._meta.es_index_name,
                              query=query)


def get_sentiment_termvector_for_text(text):
    """
    Call do_es_termvectors_for_text() and return the result
    """

    query = build_termvector_query(text=text, analyzer='termvector_sentiment_analyzer',
                                   offsets='true', positions='true')
    termvector = do_es_termvectors_for_text(index=Letter._meta.es_index_name,
                                            query=query)
    return termvector


def build_termvector_query(text, analyzer, offsets, positions):
    """
    Build a query with given analyzer, offsets, position,
    and optionally text
    """
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
    """
    Return the 'terms' portion of term_vectors contents from result,
    if they're in there
    """

    termvector = {}
    if 'term_vectors' in result \
            and 'contents' in result['term_vectors'] \
            and 'terms' in result['term_vectors']['contents']:
        termvector = result['term_vectors']['contents']['terms']

    return termvector


def get_stored_fields_for_letter(letter_id, stored_fields):
    """
    Return the Elasticsearch stored fields for letter with the given id
    """

    url = str.format('{0}{1}?stored_fields={2}', ES_LETTER_URL,
                     str(letter_id), ','.join(stored_fields))
    response = requests.get(url)
    return json.loads(response.text)


def do_es_analyze(index, query):
    """
    Return the results of Elasticsearch analyze for the given query
    """

    try:
        response = ES_CLIENT.indices.analyze(index=index,
                                             body=query)
        if 'tokens' in response:
            return response

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_mtermvectors(index, query):
    """
    Return the results of Elasticsearch mtermvector request for the given query
    """

    try:
        response = ES_CLIENT.mtermvectors(index=index, body=query)

        if 'docs' in response:
            return response

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_termvectors_for_text(index, query):
    """
    Call Elasticsearch termvectors request for the given query, call get_termvector_from_result()
    with return value, and return result
    """

    try:
        response = ES_CLIENT.termvectors(index=index,
                                         body=query)

        if 'term_vectors' in response:
            return get_termvector_from_result(response)

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_search(index, query):
    """
    Call Elasticsearch search for the given query and return result

    If there was an error, raise an exception
    """

    try:
        response = ES_CLIENT.search(index=index, body=query)

        if 'hits' in response:
            return response

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def index_temp_document(text):
    """
    Temporarily index a document to use Elasticsearch to calculate
    custom sentiment score for a piece of arbitrary text
    """

    ES_CLIENT.index(
        index=Letter._meta.es_index_name,
        id='temp',
        refresh=True,
        body={'contents': text}
    )


def delete_temp_document():
    """
    Delete temporarily indexed document from Elasticsearch index because it's not an actual transcription
    and was only used to get a score for sentiment
    """

    ES_CLIENT.delete(
        index=Letter._meta.es_index_name,
        id='temp',
        refresh=True,
    )


def raise_exception_from_response_error(response):
    """
    If response contains error, raise custom ElasticsearchException
    """
    response_json = json.loads(response.text)

    error = response_json.get('error', '')
    status = response_json.get('status', 0)
    if error:
        raise ElasticsearchException(status=status, error=error)


def raise_exception_from_request_error(request_error):
    """
    A RequestError exception was returned by the Elasticsearch client
    Raise a new custom ElasticsearchException
    """

    # exception.info contains dict of returned error info from Elasticsearch, where available
    if request_error.info:
        error = request_error.info.get('error')
        status = request_error.info.get('status')
    else:
        error = request_error.error
        status = request_error.status_code

    raise ElasticsearchException(status=status, error=error)
