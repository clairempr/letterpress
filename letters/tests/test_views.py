import json

from collections import namedtuple
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from letters.views import get_stats, letters_view


class HomeTestCase(SimpleTestCase):
    """
    Test home view
    """

    def test_home(self):
        """
        Response context should contain 'title' and 'nbar'
        """

        response = self.client.get(reverse('home'), follow=True)
        self.assertEqual(response.context['title'], 'Letterpress', "Home view context 'title' should be 'Letterpress'")
        self.assertEqual(response.context['nbar'], 'home', "Home view context 'nbar' should be 'home'")


class LettersViewTestCase(TestCase):
    """
    Test letters_view
    """

    @patch('letters.views.export', autospec=True)
    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_letters_view(self, mock_get_initial_filter_values, mock_export):
        """
        If request.method is POST, export(request) should be returned

        Otherwise, response context should contain 'title', 'nbar', 'filter_values', 'show_search_text',
        'sort_by', and 'show_export_button'
        """

        mock_export.return_value = 'export'
        mock_get_initial_filter_values.return_value = 'initial filter values'

        # POST
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('letters_view'))
        response = letters_view(request)
        self.assertEqual(response, mock_export.return_value, "letters_view() should call export() if POST request")

        # GET
        response = self.client.get(reverse('letters_view'), follow=True)

        expected = {'title': 'Letters', 'nbar': 'letters_view',
                    'filter_values': mock_get_initial_filter_values.return_value,
                    'show_search_text': 'true', 'show_export_button': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "letters_view() context '{}' should be '{}' if GET request".format(key, expected[key]))
        self.assertIn('sort_by', response.context,
                      "letters_view() context should contain 'sort_by' if GET request".format(key))


class StatsViewTestCase(TestCase):
    """
    Test stats_view
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_stats_view(self, mock_get_initial_filter_values):

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('stats_view'), follow=True)

        expected = {'title': 'Letter statistics', 'nbar': 'stats',
                    'filter_values': mock_get_initial_filter_values.return_value, 'show_words': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "stats_view() context '{}' should be '{}' if GET request".format(key, expected[key]))


class GetStatsTestCase(TestCase):
    """
    Test get_stats()

    get_stats() should show stats for requested words/months, based on filter
    """

    def setUp(self):
        self.request = RequestFactory().post(reverse('letters_view'))
        self.FilterValues = namedtuple('FilterValues',
                          ['search_text', 'source_ids', 'writer_ids', 'start_date', 'end_date',
                           'words',
                           'sentiment_ids', 'sort_by'])
        self.filter_values = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1862-01-01'],
            end_date=['1862-12-31'],
            words=['&', 'and'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )

    @patch('letters.views.letters_filter.get_filter_values_from_request', autospec=True)
    @patch('letters.views.letter_search.get_word_counts_per_month', autospec=True)
    @patch('letters.views.letter_search.get_multiple_word_frequencies', autospec=True)
    @patch('letters.views.render_to_string', autospec=True)
    @patch('letters.views.make_charts', autospec=True)
    def test_get_stats(self, mock_make_charts, mock_render_to_string, mock_get_multiple_word_frequencies,
                       mock_get_word_counts_per_month, mock_get_filter_values_from_request):
        # GET request should return ValueError
        with self.assertRaises(ValueError):
            self.client.get(reverse('get_stats'), follow=True)


        # POST request
        mock_get_filter_values_from_request.return_value = self.filter_values
        mock_get_word_counts_per_month.return_value = {'1862-01': {'total_words': 4, 'avg_words': 3, 'doc_count': 1},
                                                       '1862-02': {'total_words': 5, 'avg_words': 4, 'doc_count': 2}}
        mock_get_multiple_word_frequencies.return_value = {'1862-01': {'&': 2, 'and': 1}, '1862-02': {'&': 2, 'and': 1}}
        mock_render_to_string.return_value = 'html string'
        mock_make_charts.return_value = 'charts'

        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        response = get_stats(self.request)

        # render_to_string() should get called with certain args
        args, kwargs = mock_render_to_string.call_args
        self.assertEqual(args[1]['words'], self.filter_values.words,
                         "get_stats() should call render_to_string() with 'words' as arg")

        # If 2 words, render_to_string() should be called with 'show_proportion' True
        self.assertTrue(args[1]['show_proportion'],
                        "If 2 words, get_stats() should call render_to_string() with 'show_proportion' True")

        # make_charts() should get called with certain args
        args, kwargs = mock_make_charts.call_args
        self.assertEqual(args[0], self.filter_values.words,
                         'get_stats() should call make_charts() with filter_values.words as arg')
        self.assertEqual(args[1], ['1862-01', '1862-02'],
                         'get_stats() should call make_charts() with months as arg')

        # If 2 words in filter_values, make_charts() should be called with proportions != 0 for each month
        self.assertNotEqual(args[2], [0, 0],
            'If 2 words in filter_values, get_stats() should call make_charts() with proportions != 0 for each month')

        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['stats'], mock_render_to_string.return_value,
                         "get_stats() content['stats'] should be return value of render_to_string()")
        self.assertEqual(content['chart'], mock_make_charts.return_value,
                         "get_stats() content['charts'] should be return value of make_charts() if show_charts is true")

        # If 1 word in filter_values, make_charts() should be called with proportions == [0, 0] (0 for each month)
        mock_make_charts.reset_mock()

        filter_values_one_word = self.FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1862-01-01'],
            end_date=['1862-12-31'],
            words=['&'],
            sentiment_ids=[1, 2, 3],
            sort_by='sort_by'
        )
        mock_get_filter_values_from_request.return_value = filter_values_one_word

        get_stats(self.request)

        args, kwargs = mock_make_charts.call_args
        self.assertEqual(args[2], [0, 0],
            'If 1 word in filter_values, get_stats() should call make_charts() with proportions == 0 for each month')

        # If months not in Elasticsearch word frequencies, 'chart' in response should be empty string
        mock_get_multiple_word_frequencies.return_value = {}

        response = get_stats(self.request)
        content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(content['chart'], '',
            "If months not in Elasticsearch word frequencies, 'chart' in get_stats() response should be empty string")


class WordcloudViewTestCase(TestCase):
    """
    Test wordcloud_view()
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_wordcloud_view(self, mock_get_initial_filter_values):

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('wordcloud_view'), follow=True)

        expected = {'title': 'Word cloud', 'nbar': 'stats',
                    'filter_values': mock_get_initial_filter_values.return_value, 'show_search_text': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "wordcloud_view() context '{}' should be '{}'".format(key, expected[key]))
