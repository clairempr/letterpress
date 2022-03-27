import json

from collections import namedtuple
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, TestCase

from letters.letter_search import do_letter_search, get_doc_highlights, get_date_query, get_doc_word_count, \
    get_filter_conditions_for_query, get_highlight_options, get_letter_match_query, get_letter_sentiments, \
    get_letter_word_count, get_multiple_word_frequencies, get_sort_conditions, get_word_counts_per_month, \
    get_year_month_from_date
from letters.models import Letter
from letters.sort_by import DATE, SENTIMENT
from letters.tests.factories import LetterFactory


def get_filter_values_namedtuple():
    return namedtuple('FilterValues',
                      ['search_text', 'source_ids', 'writer_ids', 'start_date', 'end_date',
                       'words',
                       'sentiment_ids', 'sort_by'])


class DoLetterSearchTestCase(TestCase):
    """
    Based on search criteria in request, do_letter_search() should query elasticsearch and
    return list of tuples containing letter and highlight
    """

    def setUp(self):
        self.FilterValues = get_filter_values_namedtuple()
        self.filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        self.request_factory = RequestFactory()

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_search_bool_query(self, mock_format_sentiment, mock_get_letter_sentiments,
                                         mock_get_doc_highlights, mock_do_es_search,
                                         mock_get_sort_conditions,mock_get_highlight_options,
                                         mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                         mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                         mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                         mock_get_filter_values_from_request):
        """
        Test to make sure bool_query has the form
            bool_query = {
                'should': sentiment_match_query,
                'filter': get_filter_conditions_for_query(filter_values)
            }

        If letter_match_query filled, bool_query should have bool_query['must'] = letter_match_query
        added to it

        If sentiment_match_query filled, get_sentiment_function_score_query(bool_query) should be called
        """

        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_selected_sentiment_id.return_value = 'selected_sentiment_id'
        mock_get_sentiment_function_score_query.return_value = 'sentiment_function_score_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        request = self.request_factory.get('search', data={})

        # If sentiment_match_query filled, get_sentiment_function_score_query(bool_query) should be called
        mock_get_sentiment_match_query.return_value = 'sentiment_match_query'

        # If get_letter_match_query() returns something, ['must'] = letter_match_query
        # should get added to bool_query
        mock_get_letter_match_query.return_value = 'letter_match_query'
        expected_bool_query = {
            'should': mock_get_sentiment_match_query.return_value,
            'filter': mock_get_filter_conditions_for_query.return_value,
            'must': mock_get_letter_match_query.return_value
        }

        do_letter_search(request, size=1, page_number=0)

        args, kwargs = mock_get_sentiment_function_score_query.call_args
        self.assertEqual(args[0], expected_bool_query,
                "If get_letter_match_query() returns something, 'must': letter_match_query should be in bool_query")
        mock_get_sentiment_function_score_query.reset_mock()

        # If get_letter_match_query() returns nothing, ['must'] = letter_match_query
        # shouldn't get added to bool_query
        mock_get_letter_match_query.return_value = None
        expected_bool_query = {
            'should': mock_get_sentiment_match_query.return_value,
            'filter': mock_get_filter_conditions_for_query.return_value,
        }

        do_letter_search(request, size=1, page_number=0)

        args, kwargs = mock_get_sentiment_function_score_query.call_args
        self.assertEqual(args[0], expected_bool_query,
                "If get_letter_match_query() returns nothing, 'must': letter_match_query shouldn't be in bool_query")
        mock_get_sentiment_function_score_query.reset_mock()

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_search_calls(self, mock_format_sentiment, mock_get_letter_sentiments, mock_get_doc_highlights,
                                    mock_do_es_search, mock_get_sort_conditions,mock_get_highlight_options,
                                    mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                    mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                    mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                    mock_get_filter_values_from_request):
        """
        Test to make sure methods that should always get called get called:
            get_filter_values_from_request()
            get_filter_conditions_for_query()
            # get_letter_match_query()
            get_highlight_options()
            get_sort_conditions()
            do_es_search()
        """

        mock_get_filter_values_from_request.return_value = self.filter_values
        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        request = self.request_factory.get('search', data={})

        do_letter_search(request, size=1, page_number=0)

        # do_letter_search() should always call get_filter_values_from_request, get_filter_conditions_for_query,
        # get_letter_match_query, get_highlight_options, get_sort_conditions, and do_es_search
        args, kwargs = mock_get_filter_values_from_request.call_args
        self.assertEqual(args[0], request,
                         'do_letter_search() should call get_filter_values_from_request(request)')
        args, kwargs = mock_get_filter_conditions_for_query.call_args
        self.assertEqual(args[0], self.filter_values,
                         'do_letter_search() should call get_filter_conditions_for_query(filter_values)')
        args, kwargs = mock_get_letter_match_query.call_args
        self.assertEqual(args[0], self.filter_values,
                         'do_letter_search() should call get_letter_match_query(filter_values)')
        args, kwargs = mock_get_highlight_options.call_args
        self.assertEqual(args[0], self.filter_values,
                         'do_letter_search() should call get_highlight_options(filter_values)')
        args, kwargs = mock_get_sort_conditions.call_args
        self.assertEqual(args[0], self.filter_values.sort_by,
                         'do_letter_search() should call get_sort_conditions(filter_values.sort_by)')

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_search_filter_values(self, mock_format_sentiment, mock_get_letter_sentiments,
                                            mock_get_doc_highlights,
                                            mock_do_es_search, mock_get_sort_conditions, mock_get_highlight_options,
                                            mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                            mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                            mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                            mock_get_filter_values_from_request):
        """
        Test to make sure sentiment_id, sentiment_match_query, and custom_sentiment_name
        get properly filled according to what's in filter_values
        """

        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_selected_sentiment_id.return_value = 'selected_sentiment_id'
        mock_get_sentiment_function_score_query.return_value = 'sentiment_function_score_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        # If filter_values.sort_by is filled and starts with SENTIMENT,
        # get_selected_sentiment_id(), get_sentiment_match_query(), and get_custom_sentiment_name()
        # should get called, and sentiment_id, sentiment_match_query, and custom_sentiment_name should get filled
        filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by=SENTIMENT + 'some other stuff'
        )

        mock_get_filter_values_from_request.return_value = filter_values

        request = self.request_factory.get('search', data={})
        do_letter_search(request, size=1, page_number=0)

        self.assertEqual(mock_get_selected_sentiment_id.call_count, 1,
            'If filter_values.sort_by is filled and starts with SENTIMENT, get_selected_sentiment_id() should be called')
        self.assertEqual(mock_get_sentiment_match_query.call_count, 1,
            'If filter_values.sort_by is filled and starts with SENTIMENT, get_sentiment_match_query() should be called')
        self.assertEqual(mock_get_custom_sentiment_name.call_count, 1,
            'If filter_values.sort_by is filled and starts with SENTIMENT, get_custom_sentiment_name() should be called')

        mock_get_selected_sentiment_id.reset_mock()
        mock_get_sentiment_match_query.reset_mock()
        mock_get_custom_sentiment_name.reset_mock()

        # If filter_values.sort_by is filled but doesn't start with with SENTIMENT,
        # get_selected_sentiment_id(), get_sentiment_match_query(), and get_custom_sentiment_name()
        # should NOT get called, and sentiment_id, sentiment_match_query, and custom_sentiment_name should not get filled
        filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='some other stuff'
        )

        mock_get_filter_values_from_request.return_value = filter_values

        request = self.request_factory.get('search', data={})
        do_letter_search(request, size=1, page_number=0)

        self.assertEqual(mock_get_selected_sentiment_id.call_count, 0,
            "If filter_values.sort_by doesn't start with SENTIMENT, get_selected_sentiment_id() shouldn't be called")
        self.assertEqual(mock_get_sentiment_match_query.call_count, 0,
            "If filter_values.sort_by doesn't start with SENTIMENT, get_sentiment_match_query() shouldn't be called")
        self.assertEqual(mock_get_custom_sentiment_name.call_count, 0,
            "If filter_values.sort_by doesn't start with SENTIMENT, get_custom_sentiment_name() shouldn't be called")

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_search_hits(self, mock_format_sentiment, mock_get_letter_sentiments,
                                            mock_get_doc_highlights,
                                            mock_do_es_search, mock_get_sort_conditions, mock_get_highlight_options,
                                            mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                            mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                            mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                            mock_get_filter_values_from_request):
        """
        Test to make sure that if 'hits' in the return value of do_es_search(json.dumps(query_json)),
        get_doc_highlights(), get_letter_sentiments(), and format_sentiment() get called
        Otherwise they shouldn't get called
        """

        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_selected_sentiment_id.return_value = 'selected_sentiment_id'
        mock_get_sentiment_function_score_query.return_value = 'sentiment_function_score_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        # If 'hits' in the return value of do_es_search(json.dumps(query_json)),
        # get_doc_highlights(), get_letter_sentiments(), and format_sentiment() should get called
        mock_do_es_search.return_value = {'hits': {
            'hits':
                [{'_id': LetterFactory().id, '_score': 1}],
            'total': 5}
        }

        request = self.request_factory.get('search', data={})
        do_letter_search(request, size=1, page_number=0)

        self.assertEqual(mock_get_doc_highlights.call_count, 1,
                         "If 'hits' in return value of do_es_search(), get_doc_highlights() should get called")
        self.assertEqual(mock_get_letter_sentiments.call_count, 1,
                         "If 'hits' in return value of do_es_search(), get_letter_sentiments() should get called")
        self.assertEqual(mock_format_sentiment.call_count, 1,
                         "If 'hits' in return value of do_es_search(), format_sentiment() should get called")

        mock_get_doc_highlights.reset_mock()
        mock_get_letter_sentiments.reset_mock()
        mock_format_sentiment.reset_mock()

        # If 'hits' in return value of do_es_search(json.dumps(query_json)) but sentiment_id is 0,
        # format_sentiment() should not get called
        filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='some other stuff'
        )
        mock_get_filter_values_from_request.return_value = filter_values

        request = self.request_factory.get('search', data={})
        do_letter_search(request, size=1, page_number=0)

        self.assertEqual(mock_format_sentiment.call_count, 0,
            "If 'hits' in return value of do_es_search() but no sentiment_id, format_sentiment() shouldn't get called")

        mock_get_doc_highlights.reset_mock()
        mock_get_letter_sentiments.reset_mock()
        mock_format_sentiment.reset_mock()

        # If 'hits' not in the return value of do_es_search(json.dumps(query_json)),
        # get_doc_highlights(), get_letter_sentiments(), and format_sentiment() should NOT get called
        mock_do_es_search.return_value = {}

        request = self.request_factory.get('search', data={})
        do_letter_search(request, size=1, page_number=0)

        self.assertEqual(mock_get_doc_highlights.call_count, 0,
                         "If 'hits' not in return value of do_es_search(), get_doc_highlights() shouldn't get called")
        self.assertEqual(mock_get_letter_sentiments.call_count, 0,
                         "If 'hits' not in return value of do_es_search(), get_letter_sentiments() shouldn't get called")
        self.assertEqual(mock_format_sentiment.call_count, 0,
                         "If 'hits' not in return value of do_es_search(), format_sentiment() shouldn't get called")

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_search_page_number(self, mock_format_sentiment, mock_get_letter_sentiments,
                                          mock_get_doc_highlights,
                                          mock_do_es_search, mock_get_sort_conditions, mock_get_highlight_options,
                                          mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                          mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                          mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                          mock_get_filter_values_from_request):
        """
        Test to make sure do_es_search() gets called with the right value of 'from' in the query,
        depending on page_number
        """

        mock_get_filter_values_from_request.return_value = self.filter_values
        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_sentiment_function_score_query.return_value = 'sentiment_function_score_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        request_factory = RequestFactory()
        request = request_factory.get('search', data={})

        # If page_number is 0 and size is 1, do_es_search() should be called with json.dumps(query_json)
        # where query_json 'from' is 0
        do_letter_search(request, page_number=0, size=1)
        args, kwargs = mock_do_es_search.call_args
        query = json.loads(args[0])
        self.assertEqual(query['from'], 0,
                         "If page_number is 0, do_letter_search() should call do_es_search() with query where 'from' is 0")
        mock_do_es_search.reset_mock()

        # If page_number is 1 and size is 1, do_es_search() should be called with json.dumps(query_json)
        # where query_json 'from' is 0
        do_letter_search(request, page_number=1, size=1)
        args, kwargs = mock_do_es_search.call_args
        query = json.loads(args[0])
        self.assertEqual(query['from'], 0,
                         "If page_number is 1, do_letter_search() should call do_es_search() with query where 'from' is 0")
        mock_do_es_search.reset_mock()

        # If page_number is 1 and size is 1, do_es_search() should be called with json.dumps(query_json)
        # where query_json 'from' is 1
        do_letter_search(request, page_number=2, size=1)
        args, kwargs = mock_do_es_search.call_args
        query = json.loads(args[0])
        self.assertEqual(query['from'], 1,
                         "If page_number is 2, do_letter_search() should call do_es_search() with query where 'from' is 1")
        mock_do_es_search.reset_mock()

    @patch('letters.filter.get_filter_values_from_request', autospec=True)
    @patch('letters.letter_search.get_selected_sentiment_id', autospec=True)
    @patch('letters.letter_search.get_sentiment_match_query', autospec=True, return_value='sentiment_match_query')
    @patch('letters.letter_search.get_custom_sentiment_name', autospec=True, return_value='custom_sentiment_name')
    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True, return_value='filter_conditions')
    @patch('letters.letter_search.get_letter_match_query', autospec=True)
    @patch('letters.letter_search.get_sentiment_function_score_query', autospec=True)
    @patch('letters.letter_search.get_highlight_options', autospec=True, return_value='highlight_options')
    @patch('letters.letter_search.get_sort_conditions', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_doc_highlights', autospec=True)
    @patch('letters.letter_search.get_letter_sentiments', autospec=True)
    @patch('letters.letter_search.format_sentiment', autospec=True)
    def test_do_letter_result(self, mock_format_sentiment, mock_get_letter_sentiments,
                                            mock_get_doc_highlights,
                                            mock_do_es_search, mock_get_sort_conditions, mock_get_highlight_options,
                                            mock_get_sentiment_function_score_query, mock_get_letter_match_query,
                                            mock_get_filter_conditions_for_query, mock_get_custom_sentiment_name,
                                            mock_get_sentiment_match_query, mock_get_selected_sentiment_id,
                                            mock_get_filter_values_from_request):
        """
        The number of pages depends on total and size and should be calculated as follows
            if total % size:
                pages = int(total / size + 1)
            else:
                pages = int(total / size)

        do_letter_result() should return a namedtuple ES_Result,
        which contains 'search_results', 'total', and 'pages'
        """

        mock_get_letter_match_query.return_value = 'letter_match_query'
        mock_get_selected_sentiment_id.return_value = 'selected_sentiment_id'
        mock_get_sentiment_function_score_query.return_value = 'sentiment_function_score_query'
        mock_get_sort_conditions.return_value = 'sort_conditions'

        letter = LetterFactory()

        mock_do_es_search.return_value = {'hits': {
            'hits':
                [{'_id': letter.id, '_score': 1}],
            'total': 10}
        }

        request = self.request_factory.get('search', data={})

        result = do_letter_search(request, size=3, page_number=0)

        # The letter(s) in hits from do_es_search() should be returned with result
        self.assertTrue(letter in result.search_results[0],
                        'do_letter_search() search_results should include letters returned by do_es_search()')
        # Total should be returned with result
        self.assertEqual(result.total, 10,
                         'do_letter_search() total should be the total returned by do_es_search()')
        # If total not divisible by size, pages should be total / size + 1
        self.assertEqual(result.pages, 4,
                         'do_letter_search() pages should be total / size + 1 if total not divisible by size')

        # If total is divisible by size, pages should be total / size
        result = do_letter_search(request, size=5, page_number=0)
        self.assertEqual(result.pages, 2,
                         'do_letter_search() pages should be total / size if total divisible by size')


class GetDateQueryTestCase(SimpleTestCase):
    """
    get_date_query() should return date query for Elasticsearch based on date range in filter_values
    """

    def test_get_date_query(self):
        FilterValues = get_filter_values_namedtuple()
        filter_values = FilterValues(
            search_text='',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        result = get_date_query(filter_values)

        # filter_values.start_date should be in returned query
        self.assertEqual(result['range']['date']['gte'], filter_values.start_date,
                         'get_date_query() should return query that contains start_date from filter_values')
        # filter_values.end_date should be in returned query
        self.assertEqual(result['range']['date']['lte'], filter_values.end_date,
                         'get_date_query() should return query that contains end_date from filter_values')


class GetDocHighlightsTestCase(SimpleTestCase):
    """
    get_doc_highlights() should return a <br>-separated list of Elasticsearch highlights,
    if there are any
    """

    def test_get_doc_highlights(self):
        # No 'highlight' in doc
        result = get_doc_highlights(doc={})
        self.assertEqual(result, '', 'get_doc_highlights() should return an empty string if there is no highlight')

        # 'highlight' in doc but no 'contents' or 'contents.custom_sentiment' in highlight
        doc = {'highlight': 'highlight'}
        result = get_doc_highlights(doc=doc)
        self.assertEqual(result, '',
                         'get_doc_highlights() should return an empty string if there are no contents in highlight')

        # ['highlight']['contents'] in doc
        contents = ['content1', 'content2']
        doc = {'highlight': {'contents': contents}}
        result = get_doc_highlights(doc=doc)
        for content in contents:
            self.assertTrue(content in result,
                    'get_doc_highlights() should return a highlight containing contents if contents is in highlight')

        # ['highlight']['contents.custom_sentiment'] in doc
        custom_sentiments = ['custom_sentiment1', 'custom_sentiment2']
        doc = {'highlight': {'contents.custom_sentiment': custom_sentiments}}
        result = get_doc_highlights(doc=doc)
        for custom_sentiment in custom_sentiments:
            self.assertTrue(custom_sentiment in result,
                    'get_doc_highlights() should return a highlight containing contents if contents is in highlight')


class GetDocWordCountTestCase(SimpleTestCase):
    """
    get_doc_word_count() should get word_count from doc already returned from Elasticsearch query
    """

    def test_get_doc_word_count(self):
        # test_get_doc_word_count() should return 0 if 'fields' not in doc
        result = get_doc_word_count(doc={})
        self.assertEqual(result, 0, "test_get_doc_word_count() should return 0 if 'fields' not in doc")

        # test_get_doc_word_count() should return 0 if 'fields' in doc
        # but 'contents.word_count' not in fields
        doc = {'fields': 'fields'}
        result = get_doc_word_count(doc=doc)
        self.assertEqual(result, 0,
                "test_get_doc_word_count() should return 0 if 'fields' in doc but 'contents.word_count' not in fields")

        # If 'fields' in doc and 'contents.word_count' fields, test_get_doc_word_count()
        # should return doc['fields']['contents.word_count']
        word_count = 5
        doc = {'fields': {'contents.word_count': [word_count]}}
        result = get_doc_word_count(doc=doc)
        self.assertEqual(result, word_count,
            "test_get_doc_word_count() should return word_count if 'fields' in doc and 'contents.word_count' in fields")


class GetFilterConditionsForQueryTestCase(SimpleTestCase):
    """
    Get a date_query for Elasticsearch based on filter_values,
    and add 'terms' with source_ids and writer_ids if they're present in filter_values
    """

    def test_get_filter_conditions_for_query(self):
        FilterValues = get_filter_values_namedtuple()

        # If 'source_ids' and 'writer_ids' not in filter_values,
        # 'source' and 'writer' shouldn't be in returned filter conditions
        filter_values = FilterValues(
            search_text='',
            source_ids=[],
            writer_ids=[],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        result = get_filter_conditions_for_query(filter_values)
        self.assertFalse('source' in result,
                         "If 'source_ids' empty in filter_values, 'source' shouldn't be in returned filter conditions")
        self.assertFalse('writer' in result,
                         "If 'writer_ids' empty in filter_values, 'writer' shouldn't be in returned filter conditions")

        # If 'source_ids' in filter_values, 'source' should be in returned filter conditions
        filter_values = FilterValues(
            search_text='',
            source_ids=[1, 2, 3],
            writer_ids=[],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        result = get_filter_conditions_for_query(filter_values)
        # Get the error "Generator expression must be parenthesized if not sole argument"
        # when trying to use a failure message here, so leave it out for now
        self.assertTrue('source' in result[condition]['terms'] for condition in result)

        # If 'writer_ids' in filter_values, 'writer' should be in returned filter conditions
        filter_values = FilterValues(
            search_text='',
            source_ids=[],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        result = get_filter_conditions_for_query(filter_values)
        # Get the error "Generator expression must be parenthesized if not sole argument"
        # when trying to use a failure message here, so leave it out for now
        self.assertTrue('writer' in result[condition]['terms'] for condition in result)



class GetHighlightOptionsTestCase(SimpleTestCase):
    """
    get_highlight_options() should return something something to do with highlighting
    for an Elasticsearch query, depending on whether it's a custom sentiment
    """

    def test_get_highlight_options(self):
        FilterValues = get_filter_values_namedtuple()

        # If filter_values.sort_by starts with SENTIMENT, it's a custom sentiment
        filter_values = FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by=SENTIMENT + 'some other stuff'
        )

        # If it's a custom sentiment, 'pre_tags' and 'post_tags' should be in returned value
        result = get_highlight_options(filter_values)
        for key in ['pre_tags', 'post_tags']:
            self.assertIn(key, result,
                "Value returned by get_highlight_options() should include '{}' if it's a custom sentiment".format(key))

        # If filter_values.sort_by doesn't start with SENTIMENT, it's not a custom sentiment
        filter_values = FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='something'
        )

        # If it's not a custom sentiment, 'fields' should be in returned value
        result = get_highlight_options(filter_values)
        self.assertIn('fields', result,
                "Value returned by get_highlight_options() should include 'fields' if it's not a custom sentiment")


class GetLetterMatchQueryTestCase(SimpleTestCase):
    """
    get_letter_match_query() should take search_text from filter_values and return a query for contents
    """

    def test_get_letter_match_query(self):
        FilterValues = get_filter_values_namedtuple()
        filter_values = FilterValues(
            search_text='',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        # If 'search_text' not in filter_values, get_letter_match_query should return empty string
        result = get_letter_match_query(filter_values)
        self.assertEqual(result, '',
                         "If 'search_text' not in filter_values, get_letter_match_query() should return empty string")

        # If search_text contains quotes, 'match_phrase' needs to be in the result
        filter_values = FilterValues(
            search_text='"search text"',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )
        result = get_letter_match_query(filter_values)
        self.assertTrue('match_phrase' in result,
            "If search_text contains quotes, 'match_phrase' needs to be in the query returned by get_letter_match_query()")

        # If search_text doesn't contain quotes, 'match_phrase' shouldn't be in the result
        filter_values = FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1863-01-01'],
            end_date=['1863-12-31'],
            words=['word'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )
        result = get_letter_match_query(filter_values)
        self.assertFalse('match_phrase' in result,
            "If search_text doesn't contain quotes, 'match_phrase' shouldn't be in the query returned by get_letter_match_query()")


class GetLetterSentimentsTestCase(TestCase):
    """
    get_letter_sentiments() should return a list of (id, name/result)
    consisting of sentiments with sentiment_ids for letter
    """

    def setUp(self):
        self.letter = LetterFactory()

    def test_get_letter_sentiments_no_sentiment_ids(self):
        # If no sentiment_ids, get_letter_sentiments() should return []
        result = get_letter_sentiments(letter=self.letter, sentiment_ids=[])
        self.assertEqual(result, [], 'If no sentiment_ids, get_letter_sentiments() should return []')

    @patch.object(Letter, 'sentiment', autospec=True)
    @patch('letters.letter_search.get_custom_sentiment_for_letter')
    def test_get_letter_sentiments_with_sentiment_ids(self, mock_get_custom_sentiment_for_letter,
                                                      mock_letter_sentiment):
        mock_letter_sentiment.return_value = ['letter_sentiment1', 'letter_sentiment2']
        mock_get_custom_sentiment_for_letter.return_value = 'custom_sentiment'

        # If sentiment_id is 0, letter.sentiment() should get called
        # and get_custom_sentiment_for_letter() should not get called
        sentiment_ids = [0]
        result = get_letter_sentiments(letter=self.letter, sentiment_ids=sentiment_ids)
        self.assertEqual(mock_letter_sentiment.call_count, 1,
                         'If sentiment_id is 0, letter.sentiment() should get called')
        self.assertEqual(mock_get_custom_sentiment_for_letter.call_count, 0,
                         'If sentiment_id is 0, get_custom_sentiment_for_letter() should not get called')
        # (sentiment_id, letter_sentiments) should be in result
        self.assertTrue((0, mock_letter_sentiment.return_value) in result,
                        'If sentiment_id is 0, (sentiment_id, letter_sentiments) should be in result')
        mock_letter_sentiment.reset_mock()

        # If sentiment_id is not 0, get_custom_sentiment_for_letter() should get called
        # and letter.sentiment() should not get called
        sentiment_ids = [1, 2]
        result = get_letter_sentiments(letter=self.letter, sentiment_ids=sentiment_ids)
        self.assertEqual(mock_get_custom_sentiment_for_letter.call_count, 2,
                         'If sentiment_id is not 0, get_custom_sentiment_for_letter() should get called')
        self.assertEqual(mock_letter_sentiment.call_count, 0,
                         'If sentiment_id is not 0, letter.sentiment() should not get called')
        # (sentiment_id, custom_sentiment) should be in result
        for sentiment_id in sentiment_ids:
            self.assertTrue((sentiment_id, mock_get_custom_sentiment_for_letter.return_value) in result,
                            'If sentiment_id is 0, (sentiment_id, custom_sentiment) should be in result')


class GetLetterWordCountTestCase(SimpleTestCase):
    """
    get_letter_word_count() should get word_count for letter with letter_id using Elasticsearch query
    """

    @patch('letters.letter_search.get_stored_fields_for_letter', autospec=True)
    @patch('letters.letter_search.get_doc_word_count', autospec=True)
    def test_get_letter_word_count(self, mock_get_doc_word_count, mock_get_stored_fields_for_letter):
        mock_get_stored_fields_for_letter.return_value = 'stored_fields_for_letter'
        mock_get_doc_word_count.return_value = 42

        letter_id = 1

        # get_letter_word_count() should call get_stored_fields_for_letter() and get_doc_word_count()
        result = get_letter_word_count(letter_id=letter_id)
        args, kwargs = mock_get_stored_fields_for_letter.call_args
        self.assertEqual(args[0], letter_id,
                         'get_letter_word_count() should call get_stored_fields_for_letter() with letter_id as arg')
        args, kwargs = mock_get_doc_word_count.call_args
        self.assertEqual(args[0], mock_get_stored_fields_for_letter.return_value,
            'get_letter_word_count() should call get_doc_word_count() with return value of get_stored_fields_for_letter()')

        # get_letter_word_count() should return the return value of get_doc_word_count()
        self.assertEqual(result, mock_get_doc_word_count.return_value,
                         'get_letter_word_count() should return the return value of get_doc_word_count()')


class GetMultipleWordFrequenciesTestCase(SimpleTestCase):
    """
    get_multiple_word_frequencies() should get term frequencies for mtermvectors
    returned by Elasticsearch using the given filters
    """

    def setUp(self):
        self.FilterValues = get_filter_values_namedtuple()
        self.filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['&', 'and', 'torpedo'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        self.doc1_id = 1
        self.doc2_id = 2

        self.mtermvectors = {'docs':
                                 [{'_id': self.doc1_id, 'term_vectors':
                                     {'contents':
                                          {'terms': {'&': {'term_freq': 2},
                                                     'and': {'term_freq': 1}}}
                                      }
                                   },
                                  {'_id': self.doc2_id, 'term_vectors':
                                      {'contents': {'terms': {'&': {'term_freq': 1}}}}}]
                             }

        self.ampersand_total_freq = 3
        self.and_total_freq = 1

    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    @patch('letters.letter_search.get_mtermvectors', autospec=True)
    @patch('letters.letter_search.get_year_month_from_date', autospec=True)
    def test_get_multiple_word_frequencies_hits(self, mock_get_year_month_from_date, mock_get_mtermvectors,
                                                mock_do_es_search, mock_get_filter_conditions_for_query):
        mock_get_filter_conditions_for_query.return_value = [
            {'range': {'date': {'gte': ['1863-01-01'], 'lte': ['1863-12-31']}}}, {'terms': {'source': [1, 2, 3]}},
            {'terms': {'writer': [1, 2, 3]}}]
        mock_get_mtermvectors.return_value = self.mtermvectors
        mock_get_year_month_from_date.return_value = '1863-05'

        # If 'hits' not in es_result, there should be an error
        # because matching_docs won't be filled
        mock_do_es_search.return_value = {}
        with self.assertRaises(KeyError):
            get_multiple_word_frequencies(self.filter_values)


        # If 'hits' in es_result, but 'hits' not in es_result['hits'], there should be an error
        # because matching_docs won't be filled
        mock_do_es_search.return_value = {'hits': 'hits'}
        with self.assertRaises(TypeError):
            get_multiple_word_frequencies(self.filter_values)

        mock_get_mtermvectors.reset_mock()

        mock_do_es_search.return_value = {'hits':
                                              {'hits':
                                                   [{'_id': self.doc1_id, '_source': {'date': 'date'}},
                                                    {'_id': self.doc2_id, '_source': {'date': 'date'}}]
                                               }
                                          }

        get_multiple_word_frequencies(self.filter_values)

        # get_filter_conditions_for_query() should get called with filter_values as arg
        args, kwargs = mock_get_filter_conditions_for_query.call_args
        self.assertEqual(args[0], self.filter_values,
                         'get_filter_conditions_for_query() should get called with filter_values as arg')

        # get_mtermvectors() should get called
        self.assertEqual(mock_get_mtermvectors.call_count, 1,
                         'get_multiple_word_frequencies() should call get_mtermvectors()')

        # If 'docs' not in return value of get_mtermvectors(), get_year_month_from_date()
        # shouldn't get called and get_multiple_word_frequencies() should return {}
        mock_get_year_month_from_date.reset_mock()
        mock_get_mtermvectors.return_value = []
        result = get_multiple_word_frequencies(self.filter_values)
        self.assertEqual(mock_get_year_month_from_date.call_count, 0,
                    "If 'docs' not in result of get_mtermvectors(), get_year_month_from_date() shouldn't be called")
        self.assertEqual(result, {},
                    "If 'docs' not in result of get_mtermvectors(), get_multiple_word_frequencies() should return {}")

        # If 'docs' is is return value of get_mtermvectors(),
        # get_multiple_word_frequencies() should return ???
        mock_get_mtermvectors.return_value = self.mtermvectors
        result = get_multiple_word_frequencies(self.filter_values)
        word_frequencies = result[mock_get_year_month_from_date.return_value]
        self.assertEqual(word_frequencies['&'], self.ampersand_total_freq)
        self.assertEqual(word_frequencies['and'], self.and_total_freq)
        self.assertEqual(word_frequencies['torpedo'], 0)


        self.ampersand_total_freq = 3
        self.and_total_freq = 1


class GetSortConditionsTestCase(SimpleTestCase):
    """
    get_sort_conditions() should return field/order to use for sorting in Elasticsearch query,
    depending on type of sorting
    """

    def test_get_sort_conditions(self):
        # If sort_by == DATE, sort_field in returned value should be 'date' and sort_order should be 'asc'
        result = get_sort_conditions(sort_by=DATE)
        self.assertIn('date', result,
                      "If sort_by == DATE, sort_field in value returned by get_sort_conditions() should be 'date'")
        self.assertEqual(result['date']['order'], 'asc',
                         "If sort_by == DATE, sort_order in value returned by get_sort_conditions() should be 'asc'")

        # If sort_by is empty string, sort_field in returned value should be 'date' and sort_order should be 'asc'
        result = get_sort_conditions(sort_by='')
        self.assertIn('date', result,
                "If sort_by is empty string, sort_field in value returned by get_sort_conditions() should be 'date'")
        self.assertEqual(result['date']['order'], 'asc',
                "If sort_by is empty string, sort_order in value returned by get_sort_conditions() should be 'asc'")

        # If sort_by isn't DATE or empty string, get_sort_conditions() should return '_score'
        result = get_sort_conditions(sort_by=SENTIMENT)
        self.assertEqual(result, '_score',
                         "If sort_by isn't DATE or empty string, get_sort_conditions() should return '_score'")


class GetWordCountsPerMonthTestCase(SimpleTestCase):
    """
    get_word_counts_per_month() should use Elasticsearch query with aggregations to
    retrieve counts in letters written in a given month for words given in filter_values, and return them
    """

    def setUp(self):
        self.FilterValues = get_filter_values_namedtuple()
        self.filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1864-01-01'],
            end_date=['1864-12-31'],
            words=['&', 'and', 'torpedo'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

        self.doc1_id = 1
        self.doc2_id = 2

    @patch('letters.letter_search.get_filter_conditions_for_query', autospec=True)
    @patch('letters.letter_search.do_es_search', autospec=True)
    def test_get_word_counts_per_month(self,
                                       mock_do_es_search,
                                       mock_get_filter_conditions_for_query):
        mock_get_filter_conditions_for_query.return_value = [
            {'range': {'date': {'gte': ['1863-01-01'], 'lte': ['1863-12-31']}}}, {'terms': {'source': [1, 2, 3]}},
            {'terms': {'writer': [1, 2, 3]}}]

        # If 'aggregations' not in do_es_search() return value get_word_counts_per_month() should return {}
        mock_do_es_search.return_value = {}

        result = get_word_counts_per_month(self.filter_values)
        self.assertEqual(result, {},
                    "get_word_counts_per_month() should return {} if not 'aggregations' in do_es_search() return value")

        # If 'words_per_month' not in es_result['aggregations'], get_word_counts_per_month() should return {}
        mock_do_es_search.return_value = {'aggregations': 'aggregations'}

        result = get_word_counts_per_month(self.filter_values)
        self.assertEqual(result, {},
                    "get_word_counts_per_month() should return {} if not 'aggregations' in do_es_search() return value")

        # If 'words_per_month' in es_result['aggregations']
        avg_words = 42
        total_words = 84
        doc_count = 2
        mock_do_es_search.return_value = {'aggregations':
                                              {'words_per_month':
                                                   {'buckets': [{'key_as_string': 'key_as_string',
                                                                 'avg_words': {'value': avg_words},
                                                                 'total_words': {'value': total_words},
                                                                 'doc_count': doc_count}]}
                                               }
                                          }
        result = get_word_counts_per_month(self.filter_values)
        self.assertEqual(result['key_as_']['avg_words'], avg_words,
                         "get_word_counts_per_month() return value should include ['key_as_']['avg_words']")
        self.assertEqual(result['key_as_']['total_words'], total_words,
                         "get_word_counts_per_month() return value should include ['key_as_']['total_words']")
        self.assertEqual(result['key_as_']['doc_count'], doc_count,
                         "get_word_counts_per_month() return value should include ['key_as_']['doc_count']")


class GetYearMonthFromDateTestCase(SimpleTestCase):
    """
    get_year_month_from_date() should extract year/month/day from date_string
    and return YYYY-MM formatted date, with '0000' for year if date_string empty and '00' for month
    if none in date_string
    """

    def test_get_year_month_from_date(self):
        # If date_string is empty, get_year_month_from_date() should return '0000-00'
        result = get_year_month_from_date(date_string='')
        self.assertEqual(result, '0000-00',
                         "If date_string is empty, get_year_month_from_date() should return '0000-00'")

        # If only year in date_string, year-00 should be returned
        result = get_year_month_from_date(date_string='1867')
        self.assertEqual(result, '1867-00',
                         'If only year in date_string, get_year_month_from_date() should return year-00')

        # If year-month in date_string, year-month should be returned
        result = get_year_month_from_date(date_string='1867-06')
        self.assertEqual(result, '1867-06',
                         'If year-month in date_string, get_year_month_from_date() should return year-month')
