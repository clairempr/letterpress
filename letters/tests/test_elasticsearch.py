import elasticsearch
import json

from unittest.mock import MagicMock, Mock, patch, PropertyMock

from django.test import SimpleTestCase

from letterpress.exceptions import ElasticsearchException
from letters.elasticsearch import analyze_term, build_termvector_query, delete_temp_document, do_es_analyze, \
    do_es_mtermvectors, do_es_search, do_es_termvectors_for_text, get_mtermvectors, get_sentiment_termvector_for_text, \
    get_stored_fields_for_letter, get_termvector_from_result, index_temp_document
from letters.es_settings import ES_ANALYZE, ES_LETTER_URL, ES_MTERMVECTORS, ES_SEARCH
from letters.models import Letter


class AnalyzeTermTestCase(SimpleTestCase):
    """
    analyze_term(term, analyzer) should build an Elasticsearch query using analyzer and term, call do_es_analyze(query),
    and return the analyzed text if there are tokens in the result, otherwise it should return an empty string
    """

    @patch('letters.elasticsearch.do_es_analyze', autospec=True)
    def test_analyze_term(self, mock_do_es_analyze):
        term = 'term'
        analyzer = 'termvector_sentiment_analyzer'
        query = json.dumps({'analyzer': analyzer,
                            'text': term})

        mock_do_es_analyze.return_value = {
            'tokens': [{'type': '<ALPHANUM>', 'end_offset': 5, 'token': 'horse', 'start_offset': 0, 'position': 0}]}

        result = analyze_term(term, analyzer)
        args, kwargs = mock_do_es_analyze.call_args
        self.assertEqual(args[0], query,
                         'analyze_term(term, analyzer) should call do_es_analyze() with query containing them')
        self.assertTrue('horse' in result,
                        'analyze_term() should return text containing tokens returned by do_es_analyze()')

        # If there are no tokens in return value of do_es_analyze(), empty string should be returned
        mock_do_es_analyze.return_value = {'nothing'}
        result = analyze_term(term, analyzer)
        self.assertEqual(result, '',
                         "analyze_term() should return empty string if no tokens in return value of do_es_analyze()")


class BuildTermvectorQueryTestCase(SimpleTestCase):
    """
    build_termvector_query() should build a query with given analyzer, offsets, position,
    and optionally text
    """

    def test_build_termvector_query(self):
        analyzer = 'termvector_sentiment_analyzer'
        offsets = [1, 2, 3]
        positions = [3]

        # No text specified
        result = json.loads(build_termvector_query('', analyzer, offsets, positions))
        self.assertEqual(result['per_field_analyzer']['contents'], analyzer,
                'build_termvector_query(text, analyzer, offsets, postions) should build a query that contains analyzer')
        self.assertEqual(result['offsets'], offsets,
                 'build_termvector_query(text, analyzer, offsets, postions) should build a query that contains offsets')
        self.assertEqual(result['positions'], positions,
            'build_termvector_query(text, analyzer, offsets, postions) should build a query that contains positions')
        self.assertFalse('doc' in result,
            "build_termvector_query(text, analyzer, offsets, postions) query shouldn't contain 'doc' if no text given")

        # Text specified
        text = 'fanny pack succulents'
        result = json.loads(build_termvector_query(text, analyzer, offsets, positions))
        self.assertEqual(result['doc']['contents'], text,
                'build_termvector_query(text, analyzer, offsets, postions) query should contain text if text given')


class DeleteTempDocumentTestCase(SimpleTestCase):
    """
    delete_temp_document() delete temporarily indexed document from Elasticsearch index
    """

    @patch('letters.elasticsearch.ES_CLIENT.delete')
    def test_delete_temp_document(self, mock_delete):
        result = delete_temp_document()

        args, kwargs = mock_delete.call_args
        self.assertEqual(kwargs['id'], 'temp',
                         "delete_temp_document() should call ES_CLIENT.delete() with 'id' in kwargs")
        self.assertIsNone(result, "delete_temp_document() shouldn't return anything")



class DoEsAnalyzeTestCase(SimpleTestCase):
    """
    do_es_analyze(query) should return the results of Elasticsearch analyze for the given query
    """

    def test_do_es_analyze(self):
        response_text = {'response': 'response'}

        with patch('requests.get', autospec=True,
            return_value=Mock(text=json.dumps(response_text), status_code=200)) as mock_requests_get:

            query = {'query'}
            result = do_es_analyze(query)

            args, kwargs = mock_requests_get.call_args
            self.assertEqual(args[0], ES_ANALYZE,
                             'do_es_analyze(query) should make Elasticsearch request with ES_ANALYZE as url')
            self.assertEqual(kwargs['data'], query,
                             'do_es_analyze(query) should make Elasticsearch request with query as data')
            self.assertEqual(result, response_text,
                             'do_es_analyze(query) should return result of Elasticsearch request')


class DoEsMtermvectorsTestCase(SimpleTestCase):
    """
    Return the results of Elasticsearch mtermvector request for the given query
    """

    def test_do_es_mtermvectors(self):
        response_text = {'response': 'response'}

        with patch('requests.get', autospec=True,
            return_value=Mock(text=json.dumps(response_text), status_code=200)) as mock_requests_get:

            query = {'query'}
            result = do_es_mtermvectors(query)

            args, kwargs = mock_requests_get.call_args
            self.assertEqual(args[0], ES_MTERMVECTORS,
                             'do_es_mtermvectors(query) should make Elasticsearch request with ES_MTERMVECTORS as url')
            self.assertEqual(kwargs['data'], query,
                             'do_es_mtermvectors(query) should make Elasticsearch request with query as data')
            self.assertEqual(result, response_text,
                             'do_es_mtermvectors(query) should return result of Elasticsearch request')


class DoEsSearchTestCase(SimpleTestCase):
    """
    do_es_search(index, query) should call Elasticsearch search for the given index and query,
    and return the result
    """

    def test_do_es_search(self):
        response_mock = MagicMock()
        type(response_mock).status_code = PropertyMock(return_value=200)

        query = {
            "query": {
                "query_string": {
                    "default_field": "content",
                    "query": "horse OR pony"
                }
            }
        }

        # If there was no error, search result should be returned
        with patch('elasticsearch.Elasticsearch.search', autospec=True,
            return_value=response_mock) as mock_Elasticsearch_search:
            response_mock.text = json.dumps({'search_response': 'response'})

            response = do_es_search(index=Letter._meta.es_index_name, query=query)

            args, kwargs = mock_Elasticsearch_search.call_args
            self.assertEqual(kwargs['index'], Letter._meta.es_index_name,
                             'do_es_search(query) should make Elasticsearch request with Elasticsearch.search')
            self.assertEqual(kwargs['body'], query,
                             'do_es_search(query) should make Elasticsearch request with query as data')
            self.assertTrue('search_response' in response.text,
                             'do_es_search(query) should return result of Elasticsearch request')

        # If there was an error in the response, ElasticsearchException should be raised
        with patch('elasticsearch.Elasticsearch.search', autospec=True,
            return_value=response_mock) as mock_Elasticsearch_search:
            response_mock.text = json.dumps({'error': 'Something went wrong'})

            with self.assertRaises(ElasticsearchException):
                do_es_search(index=Letter._meta.es_index_name, query=query)

        # If there was an Elasticsearch client RequestError, ElasticsearchException should be raised
        with patch('elasticsearch.Elasticsearch.search', autospec=True) as mock_Elasticsearch_search:
            request_error = elasticsearch.exceptions.RequestError

            # If exception.info filled, get error and status code from that
            request_error.info = {'error': 'Something sent wrong', 'status': 400}
            mock_Elasticsearch_search.side_effect = request_error

            with self.assertRaises(ElasticsearchException) as context:
                do_es_search(index=Letter._meta.es_index_name, query=query)
            self.assertEqual(context.exception.error, 'Something sent wrong')
            self.assertEqual(context.exception.status, 400)

            # If exception.error and exception.status_code filled, get error and status code from that
            request_error.info = None
            request_error.error = 'Something sent wrong'
            request_error.status_code = 400
            mock_Elasticsearch_search.side_effect = request_error

            with self.assertRaises(ElasticsearchException) as context:
                do_es_search(index=Letter._meta.es_index_name, query=query)
            self.assertEqual(context.exception.error, 'Something sent wrong')
            self.assertEqual(context.exception.status, 400)


class DoEsTermvectorsForTextTestCase(SimpleTestCase):
    """
    do_es_termvectors_for_text() should call Elasticsearch termvectors request for the given query,
    call get_termvector_from_result() with return value, and return result
    """

    @patch('letters.elasticsearch.get_termvector_from_result', autospec=True)
    def test_do_es_termvectors_for_text(self, mock_get_termvector_from_result):
        mock_get_termvector_from_result.return_value = 'termvector from result'

        response_text = {'response': 'response'}

        with patch('requests.get', autospec=True,
            return_value=Mock(text=json.dumps(response_text), status_code=200)) as mock_requests_get:

            query = {'query'}
            result = do_es_termvectors_for_text(query)

            args, kwargs = mock_requests_get.call_args
            self.assertTrue(ES_LETTER_URL in args[0],
                'do_es_termvectors_for_text(query) should make Elasticsearch request with ES_LETTER_URL in url')
            self.assertEqual(kwargs['data'], query,
                'do_es_termvectors_for_text(query) should make Elasticsearch request with query as data')
            args, kwargs = mock_get_termvector_from_result.call_args
            self.assertEqual(args[0], response_text,
                'do_es_termvectors_for_text(query) should call get_termvector_from_result() with result from Elasticsearch termvectors request')
            self.assertEqual(result, mock_get_termvector_from_result.return_value,
                'do_es_termvectors_for_text(query) should return result of Elasticsearch termvectors request')


class GetMtermvectorsTestCase(SimpleTestCase):
    """
    get_mtermvectors(ids, fields) should build an Elasticsearch query, using ids and fields,
    call do_es_mtermvectors(query), and return its return value
    """

    @patch('letters.elasticsearch.do_es_mtermvectors', autospec=True)
    def test_get_mtermvectors(self, mock_do_es_mtermvectors):
        mock_do_es_mtermvectors.return_value = {'es_termvectors'}

        ids = [1, 2, 3]
        fields = ['name', 'date']

        result = get_mtermvectors(ids, fields)

        args, kwargs = mock_do_es_mtermvectors.call_args
        for id in ids:
            self.assertTrue(str(id) in args[0],
                            'get_mtermvectors(ids, fields) should call do_es_mtermvectors() with query containing ids')
        for field in fields:
            self.assertTrue(field in args[0],
                        'get_mtermvectors(ids, fields) should call do_es_mtermvectors() with query containing fields')
        self.assertEqual(result, mock_do_es_mtermvectors.return_value,
                         'get_mtermvectors() should return the return value of do_es_mtermvectors()')


class GetSentimentTermvectorForTextTestCase(SimpleTestCase):
    """
    get_sentiment_termvector_for_text(text) should build a query for that text using build_termvector_query(),
    call do_es_termvectors_for_text() with that query, and return the result
    """

    @patch('letters.elasticsearch.build_termvector_query', autospec=True)
    @patch('letters.elasticsearch.do_es_termvectors_for_text', autospec=True)
    def test_get_sentiment_termvector_for_text(self, mock_do_es_termvectors_for_text, mock_build_termvector_query):
        mock_build_termvector_query.return_value = 'query'
        mock_do_es_termvectors_for_text.return_value = 'termvector'

        text = 'air plant offal'

        result = get_sentiment_termvector_for_text(text)
        args, kwargs = mock_build_termvector_query.call_args
        self.assertEqual(kwargs['text'], text,
                         'get_sentiment_termvector_for_text() should call build_termvector_query() with text=text')
        args, kwargs = mock_do_es_termvectors_for_text.call_args
        self.assertEqual(args[0], mock_build_termvector_query.return_value,
            'get_sentiment_termvector_for_text() should call do_es_termvectors_for_text() with return value of build_termvector_query')
        self.assertEqual(result, mock_do_es_termvectors_for_text.return_value,
                'get_sentiment_termvector_for_text() should return the return value of do_es_termvectors_for_text()')


class GetStoredFieldsForLetterTestCase(SimpleTestCase):
    """
    get_stored_fields_for_letter() should make a request to ES_LETTER_URL with stored_fields and letter_id
    and return the json response
    """

    def test_get_stored_fields_for_letter(self):

        response_text = {'stored_fields': 'stored fields'}

        with patch('requests.get', autospec=True,
            return_value=Mock(text=json.dumps(response_text), status_code=200)) as mock_requests_get:

            letter_id = 123
            stored_fields = ['name', 'date']

            result = get_stored_fields_for_letter(letter_id, stored_fields)
            args, kwargs = mock_requests_get.call_args
            self.assertTrue(str(letter_id) in args[0],
                            'get_stored_fields_for_letter() should make request to url containing letter_id')
            for stored_field in stored_fields:
                self.assertTrue(stored_field in args[0],
                                'get_stored_fields_for_letter() should make request to url containing stored_fields')
            self.assertEqual(result, response_text,
                             'get_stored_fields_for_letter() should return response.text from Elasticsearch request')


class GetTermvectorFromResultTestCase(SimpleTestCase):
    """
    get_termvector_from_result() should return the 'terms' portion of term_vectors contents from result,
    if they're in there, othewise it should return {}
    """

    def test_get_termvector_from_result(self):
        # If no ['term_vectors']['contents']['terms'] in result, "{}" should be returned
        result = {'stuff': 'more stuff'}
        termvector = get_termvector_from_result(result)
        self.assertEqual(termvector, {},
                         "If no ['term_vectors']['contents']['terms'] in result, '{}' should be returned")

        # If ['term_vectors']['contents']['terms'] in result, terms should be returned
        result = {'term_vectors': {'contents': {'terms': 'the terms'}}}
        termvector = get_termvector_from_result(result)
        self.assertEqual(termvector, 'the terms',
                         "If ['term_vectors']['contents']['terms'] in result, terms should be returned")


class IndexTempDocumentTestCase(SimpleTestCase):
    """
    index_temp_document(text) should temporarily index a document to use elasticsearch to calculate
    custom sentiment score for a piece of arbitrary text
    """

    @patch('letters.elasticsearch.ES_CLIENT.index')
    def test_index_temp_document(self, mock_index):
        text = 'normcore unicorn'

        result = index_temp_document(text)

        args, kwargs = mock_index.call_args
        self.assertEqual(kwargs['id'], 'temp',
                         "test_index_temp_document(text) should call ES_CLIENT.index() with 'id' in kwargs")
        self.assertEqual(kwargs['body'], {'contents': text},
                         'test_index_temp_document(text) should call ES_CLIENT.index() with text in one of the kwargs')
        self.assertIsNone(result, "test_index_temp_document(text) shouldn't return anything")
