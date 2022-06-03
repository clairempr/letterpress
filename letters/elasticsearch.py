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

    result = do_es_analyze(index=Letter._meta.es_index_name, analyzer=analyzer, text=term)
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


    return do_es_mtermvectors(index=Letter._meta.es_index_name,
                              field_statistics=False, fields=fields, ids=ids, offsets=False,
                              positions=False)


def get_sentiment_termvector_for_text(text):
    """
    Call do_es_termvectors_for_text() and return the result
    """

    termvector = do_es_termvectors_for_text(index=Letter._meta.es_index_name, doc={"contents": text},
                                            field_statistics=False,
                                            fields=["contents"],
                                            offsets=True,
                                            per_field_analyzer={"contents": "termvector_sentiment_analyzer"},
                                            positions=True)
    return termvector


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


def do_es_analyze(index, analyzer, text):
    """
    Return the results of Elasticsearch analyze for the given query
    """

    try:
        response = ES_CLIENT.indices.analyze(index=index,
                                             analyzer=analyzer,
                                             text=text)
        if 'tokens' in response:
            return response

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_mtermvectors(index, field_statistics=None, fields=None, ids=None, offsets=None,
                              positions=None):
    """
    Return the results of Elasticsearch mtermvector request for the given query
    """

    try:
        response = ES_CLIENT.mtermvectors(index=index, field_statistics=field_statistics, fields=fields,
                                          ids=ids, offsets=offsets, positions=positions)
        if 'docs' in response:
            return response

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_termvectors_for_text(index, doc=None, field_statistics=None, fields=None, offsets=None,
                               per_field_analyzer=None, positions=None):
    """
    Call Elasticsearch termvectors request for the given query, call get_termvector_from_result()
    with return value, and return result
    """

    try:
        response = ES_CLIENT.termvectors(index=index, doc=doc, field_statistics=field_statistics,
                                         fields=fields, offsets=offsets, per_field_analyzer=per_field_analyzer,
                                         positions=positions)

        if 'term_vectors' in response:
            return get_termvector_from_result(response)

        # Query didn't find anything, probably because there was an error with Elasticsearch
        raise_exception_from_response_error(response)

    except elasticsearch.exceptions.RequestError as exception:
        # Error with Elasticsearch client
        raise_exception_from_request_error(exception)


def do_es_search(index, query=None, aggs=None, from_offset=None, size=None, highlight=None, source=None,
                 stored_fields=None, sort=None):
    """
    Call Elasticsearch search for the given query and return result

    If there was an error, raise an exception
    """

    try:
        response = ES_CLIENT.search(index=index, query=query, aggs=aggs, from_=from_offset, size=size,
                                    highlight=highlight, source=source, stored_fields=stored_fields, sort=sort)

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

    status = request_error.status_code
    # exception.info contains dict of returned error info from Elasticsearch, where available
    if request_error.body:
        root_cause = request_error.body["error"]["root_cause"][0]
        error = root_cause.get('reason')
    else:
        error = request_error.error

    raise ElasticsearchException(status=status, error=error)
