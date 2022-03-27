import json

from unittest.mock import patch

from django.http.request import QueryDict
from django.test import RequestFactory, SimpleTestCase, TestCase

from letter_sentiment.models import CustomSentiment
from letter_sentiment.tests.factories import CustomSentimentFactory
from letters.filter import DEFAULT_STATS_SEARCH_WORDS, get_end_date_from_request, get_filter_values_from_request, \
    get_initial_filter_values, get_sentiment_list, get_start_date_from_request
from letters.models import Letter
from letters.tests.factories import CorrespondentFactory, DocumentSourceFactory, LetterFactory


class GetEndDateFromRequestTestCase(SimpleTestCase):
    """
    get_end_date_from_request() return the end_date from request parameters if it's there
    and '9999-12-31' otherwise
    """

    def test_get_end_date_from_request(self):
        request_factory = RequestFactory()

        # GET request
        # If there's an end date, it should be returned
        data = {'end_date': '1862-09-17'}
        request = request_factory.get('search', data=data)
        result = get_end_date_from_request(request)
        self.assertEqual(result, data['end_date'],
                         'get_end_date_from_request() should return end_date from GET request')
        # If there's no end date, '9999-12-31' should be returned
        request = request_factory.get('search', data={})
        result = get_end_date_from_request(request)
        self.assertEqual(result, '9999-12-31',
                "get_end_date_from_request() should return '9999-12-31' from GET request if none in GET parameters")

        # POST request
        # If there's an end date, it should be returned
        request = request_factory.post('search', data=data)
        result = get_end_date_from_request(request)
        self.assertEqual(result, data['end_date'],
                         'get_end_date_from_request() should return end_date from POST request')
        # If there's no end date, '9999-12-31' should be returned
        request = request_factory.post('search', data={})
        result = get_end_date_from_request(request)
        self.assertEqual(result, '9999-12-31',
                "get_end_date_from_request() should return '9999-12-31' from POST request if none in GET parameters")


class GetFilterValuesFromRequestTestCase(SimpleTestCase):
    """
    get_filter_values_from_request() should get filter values entered by user
    """

    def setUp(self):
        self.request_factory = RequestFactory()
        self.search_text = 'literally iceland'
        self.search_data = {
            'search_text': self.search_text, 'source_ids': [], 'writers': [], 'words': [], 'sentiments': [],
            'sort_by': 'start_date'
        }
        self.get = None
        self.ajax = None


    @patch.object(QueryDict, 'getlist', autospec=True)
    @patch('letters.filter.get_start_date_from_request', autospec=True)
    @patch('letters.filter.get_end_date_from_request', autospec=True)
    def get_filter_values_from_request(self, mock_get_end_date_from_request, mock_get_start_date_from_request, mock_getlist):
        """
        Test get_filter_values_from_request() with Ajax = True/False and GET = True/False
        """

        mock_getlist.return_value = [1, 2, 3]
        mock_get_start_date_from_request.return_value = '1864-02-03'
        mock_get_end_date_from_request.return_value = '1900-12-17'

        # Create an instance of an Ajax GET or POST request.
        if self.get:
            if self.ajax:
                # GET and Ajax
                request = self.request_factory.get('search', data=self.search_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            else:
                # GET and non-Ajax
                request = self.request_factory.get('search', data=self.search_data)
        else:
            # POST and Ajax
            if self.ajax:
                request = self.request_factory.post('search', data=self.search_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            else:
                # POST and non-Ajax
                request = self.request_factory.post('search', data=self.search_data)

        result = get_filter_values_from_request(request)

        # Ajax requests should call getlist 2 times, and non-Ajax requests should call it 4 times,
        # because with Ajax, words and sentiment_ids should be empty list
        if self.ajax:
            self.assertEqual(mock_getlist.call_count, 4,
                             "get_filter_values_from_request() should call getlist() 4 times if it's an Ajax call")
        else:
            self.assertEqual(mock_getlist.call_count, 2,
                            "get_filter_values_from_request() should call getlist() 2 times if it's a non-Ajax call")
        args, kwargs = mock_get_start_date_from_request.call_args
        self.assertEqual(args[0], request,
                         'get_filter_values_from_request() should call get_start_date_from_request(request)')
        args, kwargs = mock_get_end_date_from_request.call_args
        self.assertEqual(args[0], request,
                         'get_filter_values_from_request() should call mock_get_end_date_from_request(request)')

        # Check that the right values are returned
        self.assertEqual(result.search_text, self.search_text,
                         'get_filter_values_from_request() should return search_text')
        self.assertEqual(result.source_ids, mock_getlist.return_value,
                         'get_filter_values_from_request() should return source_ids')
        self.assertEqual(result.writer_ids, mock_getlist.return_value,
                         'get_filter_values_from_request() should return writer_ids')
        self.assertEqual(result.start_date, mock_get_start_date_from_request.return_value,
                         'get_filter_values_from_request() should return start_date')
        self.assertEqual(result.end_date, mock_get_end_date_from_request.return_value,
                         'get_filter_values_from_request() should return end_date')

        if self.ajax:
            self.assertEqual(result.words, mock_getlist.return_value,
                             'If Ajax request, get_filter_values_from_request() should return words')
            self.assertEqual(result.sentiment_ids, mock_getlist.return_value,
                             'If Ajax request, get_filter_values_from_request() should return sentiment_ids')
        else:
            self.assertEqual(result.words, [],
                             'If non-Ajax request, get_filter_values_from_request() should return empty for words')
            self.assertEqual(result.sentiment_ids, [],
                    'If non-Ajax request, get_filter_values_from_request() should return empty list for sentiment_ids')

        self.assertEqual(result.sort_by, 'start_date',
                         'get_filter_values_from_request() should return sort_by')

    def test_get_filter_values_from_various_requests(self):
        """
        Test Ajax/non-Ajax GET/POST request
        """

        for get in [True, False]:
            self.get = get
            for ajax in [True, False]:
                self.ajax = ajax

                self.get_filter_values_from_request()


class GetInitialFilterValuesTestCase(TestCase):
    """
    get_initial_filter_values() should return a dict containing lists of writers, start_date,
    end_date, default search words, and sentiments
    """

    @patch('letters.filter.get_sentiment_list', autospec=True)
    def test_get_initial_filter_values(self, mock_get_sentiment_list):
        mock_get_sentiment_list.return_value = ['Hipster', 'OMG Ponies!!!']

        # If there are no letters, start_date and end_date should be empty strings
        with patch.object(Letter, 'index_date', autospec=True, return_value=''):
            result = get_initial_filter_values()

            self.assertEqual(result['start_date'], '', 'If there are no letters, start_date should be empty string')
            self.assertEqual(result['end_date'], '', 'Ifthere are no letters, end_date should be empty string')
            mock_get_sentiment_list.reset_mock()

        doc_source1 = DocumentSourceFactory(name='Document source 1')
        doc_source2 = DocumentSourceFactory(name='Document source 2')
        correspondent1 = CorrespondentFactory()
        correspondent2 = CorrespondentFactory()
        LetterFactory(source=doc_source1, writer=correspondent1, date='1857-6-15')
        LetterFactory(source=doc_source2, writer=correspondent2, date='1863-1-1')

        result = get_initial_filter_values()
        self.assertEqual(mock_get_sentiment_list.call_count, 1,
                         'get_initial_filter_values() should call get_sentiment_list()')

        # If the letters are dated, start_date and end_date should be filled
        self.assertEqual(result['start_date'], '1857-06-15', 'If letters are dated, start_date should be filled')
        self.assertEqual(result['end_date'], '1863-01-01', 'If letters are dated, end_date should be filled')

        self.assertEqual(result['sources'], [doc_source1, doc_source2],
                         'get_initial_filter_values() should return list of letter sources')
        self.assertEqual(result['writers'], sorted([correspondent1, correspondent2]),
                         'get_initial_filter_values() should return list of letter writers')
        self.assertEqual(result['words'], DEFAULT_STATS_SEARCH_WORDS,
                         'get_initial_filter_values() should return default stats search words')
        self.assertEqual(result['sentiments'], mock_get_sentiment_list.return_value,
                         'get_initial_filter_values() should return list of sentiments')


class GetSentimentListTestCase(TestCase):
    """
    get_sentiment_list() should return a list of sentiments, both standard and custom,
    in named tuple with id and name
    """

    @patch('letters.filter.get_custom_sentiments', autospec=True)
    def test_get_sentiment_list(self, mock_get_custom_sentiments):
        hipster_custom_sentiment = CustomSentimentFactory(name='Hipster')
        pony_custom_sentiment = CustomSentimentFactory(name='OMG Ponies!!!')

        mock_get_custom_sentiments.return_value = {hipster_custom_sentiment, pony_custom_sentiment}

        result = get_sentiment_list()

        self.assertEqual(mock_get_custom_sentiments.call_count, 1,
                         'get_sentiment_list() should call get_custom_sentiments()')
        # One of the sentiments returned should be "Positive/negative, with id 0"
        self.assertIn((0, 'Positive/negative'), result,
                      "get_sentiment_list() should return a 'Positive/negative' sentiment")
        for sentiment in [hipster_custom_sentiment, pony_custom_sentiment]:
            self.assertIn((sentiment.id, sentiment.name), result,
                      "get_sentiment_list() should return all custom sentiments")


class GetStartDateFromRequestTestCase(SimpleTestCase):
    """
    get_start_date_from_request() should return the start_date from request parameters if it's there
    and '0001-01-01' otherwise
    """

    def test_get_start_date_from_request(self):
        request_factory = RequestFactory()

        # GET request
        # If there's a start date, it should be returned
        data = {'start_date': '1862-09-17'}
        request = request_factory.get('search', data=data)
        result = get_start_date_from_request(request)
        self.assertEqual(result, data['start_date'],
                         'get_start_date_from_request() should return start_date from GET request')
        # If there's no start date, '0001-01-01' should be returned
        request = request_factory.get('search', data={})
        result = get_start_date_from_request(request)
        self.assertEqual(result, '0001-01-01',
                "get_start_date_from_request() should return '0001-01-01' from GET request if none in GET parameters")

        # POST request
        # If there's a start date, it should be returned
        request = request_factory.post('search', data=data)
        result = get_start_date_from_request(request)
        self.assertEqual(result, data['start_date'],
                         'get_start_date_from_request() should return start_date from POST request')
        # If there's no start date, '0001-01-01' should be returned
        request = request_factory.post('search', data={})
        result = get_start_date_from_request(request)
        self.assertEqual(result, '0001-01-01',
                "get_start_date_from_request() should return '0001-01-01' from POST request if none in GET parameters")
