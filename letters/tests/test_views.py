import base64
import collections
import json

from collections import namedtuple
from matplotlib.colors import LinearSegmentedColormap
from unittest.mock import MagicMock, patch
from wordcloud import WordCloud

from django.contrib.gis.geos import Point
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from letters.models import Correspondent, Letter
from letters.tests.factories import LetterFactory, PlaceFactory
from letters.views import export_csv, export_text, get_highlighted_letter_sentiment, get_letter_export_text, \
    GetStatsView, GetTextSentimentView, GetWordCloudView, highlight_for_sentiment, highlight_letter_for_sentiment, \
    LettersView, PlaceSearchView, RandomLetterView, SearchView, show_letter_content


class LettersViewTestCase(TestCase):
    """
    Test LettersView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_letters_view_get(self, mock_get_initial_filter_values):
        """
        Response context should contain 'title', 'nbar', 'filter_values', 'show_search_text',
        'sort_by', and 'show_export_button'
        """

        mock_get_initial_filter_values.return_value = 'initial filter values'

        # GET
        response = self.client.get(reverse('letters_view'), follow=True)
        self.assertTemplateUsed(response, 'letters.html')

        expected = {'title': 'Letters', 'nbar': 'letters_view',
                    'filter_values': mock_get_initial_filter_values.return_value,
                    'show_search_text': 'true', 'show_export_button': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "LettersView context '{}' should be '{}' if GET request".format(key, expected[key]))
        self.assertIn('sort_by', response.context,
                      "LettersView context should contain 'sort_by' if GET request".format(key))

    @patch('letters.views.letter_search.do_letter_search', autospec=True)
    @patch('letters.views.export_text', autospec=True)
    @patch('letters.views.export_csv', autospec=True)
    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_letters_view_post(self, mock_get_initial_filter_values, mock_export_csv, mock_export_text,
                               mock_do_letter_search):
        """
        If request.method is POST, export_text or export_csv should be called
        """

        letter = LetterFactory()

        ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
        search_results = [(letter, 'highlight', [('1', 'sentiment')], 'score')]
        es_result = ES_Result(search_results=search_results, total=42, pages=4)

        mock_do_letter_search.return_value = es_result

        # POST
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('letters_view'))

        # If export_text is in POST parameters, export_text() should get called
        request.POST = {'export_text': True}
        LettersView().post(request)

        args, kwargs = mock_export_text.call_args
        self.assertEqual(args[0], [letter],
                         "LettersView should call export_text() if 'export_text' in POST parameters")
        self.assertEqual(mock_export_csv.call_count, 0,
                         "LettersView shouldn't call export_csv() if 'export_text' in POST parameters")
        mock_export_text.reset_mock()

        # If export_text not in POST parameters, export_csv() should get called
        request.POST = {'export_csv': True}
        LettersView().post(request)

        args, kwargs = mock_export_csv.call_args
        self.assertEqual(args[0], [letter],
                         "LettersView should call mock_export_csv(letters) if 'export_text' not in POST parameters")
        self.assertEqual(mock_export_text.call_count, 0,
                         "LettersView shouldn't call export_text() if 'export_text' not in POST parameters")
        mock_export_csv.reset_mock()


class StatsViewTestCase(SimpleTestCase):
    """
    Test StatsView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_stats_view(self, mock_get_initial_filter_values):

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('stats_view'), follow=True)
        self.assertTemplateUsed(response, 'stats.html')

        expected = {'title': 'Letter statistics', 'nbar': 'stats',
                    'filter_values': mock_get_initial_filter_values.return_value, 'show_words': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "StatsView context '{}' should be '{}' if GET request".format(key, expected[key]))


class GetStatsViewTestCase(SimpleTestCase):
    """
    Test GetStatsView

    GetStatsView should retrieve stats for requested words/months, based on filter
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
    def test_get_stats_view(self, mock_make_charts, mock_render_to_string, mock_get_multiple_word_frequencies,
                       mock_get_word_counts_per_month, mock_get_filter_values_from_request):

        # GET request should return HttpResponseNotAllowed
        response = self.client.get(reverse('get_stats'), follow=True)
        self.assertEqual(response.status_code, 405,
                         'Making a GET request to GetStatsView should return HttpResponseNotAllowed')

        # POST request
        mock_get_filter_values_from_request.return_value = self.filter_values
        mock_get_word_counts_per_month.return_value = {'1862-01': {'total_words': 4, 'avg_words': 3, 'doc_count': 1},
                                                       '1862-02': {'total_words': 5, 'avg_words': 4, 'doc_count': 2}}
        mock_get_multiple_word_frequencies.return_value = {'1862-01': {'&': 2, 'and': 1}, '1862-02': {'&': 2, 'and': 1}}
        mock_render_to_string.return_value = 'html string'
        mock_make_charts.return_value = 'charts'

        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        response = GetStatsView().post(self.request)

        # render_to_string() should get called with certain args
        args, kwargs = mock_render_to_string.call_args
        self.assertEqual(args[1]['words'], self.filter_values.words,
                         "GetStatsView should call render_to_string() with 'words' as arg")

        # If 2 words, render_to_string() should be called with 'show_proportion' True
        self.assertTrue(args[1]['show_proportion'],
                        "If 2 words, GetStatsView should call render_to_string() with 'show_proportion' True")

        # make_charts() should get called with certain args
        args, kwargs = mock_make_charts.call_args
        self.assertEqual(args[0], self.filter_values.words,
                         'GetStatsView should call make_charts() with filter_values.words as arg')
        self.assertEqual(args[1], ['1862-01', '1862-02'],
                         'GetStatsView should call make_charts() with months as arg')

        # If 2 words in filter_values, make_charts() should be called with proportions != 0 for each month
        self.assertNotEqual(args[2], [0, 0],
            'If 2 words in filter_values, GetStatsView should call make_charts() with proportions != 0 for each month')

        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['stats'], mock_render_to_string.return_value,
                         "GetStatsView content['stats'] should be return value of render_to_string()")
        self.assertEqual(content['chart'], mock_make_charts.return_value,
                         "GetStatsView content['charts'] should be return value of make_charts() if show_charts is true")

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

        GetStatsView().post(self.request)

        args, kwargs = mock_make_charts.call_args
        self.assertEqual(args[2], [0, 0],
            'If 1 word in filter_values, GetStatsView should call make_charts() with proportions == 0 for each month')

        # If months not in Elasticsearch word frequencies, 'chart' in response should be empty string
        mock_get_multiple_word_frequencies.return_value = {}

        response = GetStatsView().post(self.request)
        content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(content['chart'], '',
            "If months not in Elasticsearch word frequencies, 'chart' in GetStatsView response should be empty string")


class WordCloudViewTestCase(SimpleTestCase):
    """
    Test WordCloudView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_wordcloud_view(self, mock_get_initial_filter_values):

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('wordcloud_view'), follow=True)
        self.assertTemplateUsed(response, 'wordcloud.html')

        expected = {'title': 'Word cloud', 'nbar': 'stats',
                    'filter_values': mock_get_initial_filter_values.return_value, 'show_search_text': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "WordCloudView context '{}' should be '{}'".format(key, expected[key]))


class GetWordCloudViewTestCase(TestCase):
    """
    Test GetWordCloudView
    """

    @patch('letters.views.letter_search.do_letter_search', autospec=True)
    @patch.object(Letter, 'contents', autospec=True)
    @patch('numpy.array', autospec=True)
    @patch('letters.views.LinearSegmentedColormap', autospec=True)
    @patch('letters.views.WordCloud', autospec=True)
    @patch.object(base64, 'b64encode', autospec=True)
    def test_get_wordcloud_view(self, mock_b64encode, mock_WordCloud, mock_LinearSegmentedColormap, mock_numpy_array,
                           mock_contents, mock_do_letter_search):
        # POST request should return HttpResponseNotAllowed
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('get_wordcloud'))
        response = GetWordCloudView().dispatch(request)
        self.assertEqual(response.status_code, 405,
                         'Making a POST request to GetWordCloudView should return HttpResponseNotAllowed')

        # GET
        # If no letters returned by Elasticsearch, response content['wc'] should be empty string
        response = self.client.get(reverse('get_wordcloud'), follow=True)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['wc'], '',
                    "GetWordCloudView should return '' in response content['wc'] if no letters found by Elasticsearch")

        # If something returned by Elasticsearch, decoded WordCloud image should get returned in response content['wc']
        ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
        search_results = [(LetterFactory(), 'highlight', 'sentiment', 'score')]
        es_result = ES_Result(search_results=search_results, total=42, pages=4)

        mock_do_letter_search.return_value = es_result
        mock_contents.return_value = 'letter contents'
        mock_WordCloud.return_value = MagicMock()
        mock_b64encode.return_value.decode.return_value = 'decoded image string'

        response = self.client.get(reverse('get_wordcloud'), follow=True)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['wc'], 'decoded image string',
                         "GetWordCloudView should return decoded WordCloud image in response content['wc']")


class SentimentViewTestCase(SimpleTestCase):
    """
    Test SentimentView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    @patch('letters.views.get_sentiments_for_sort_by_list', autospec=True)
    def test_sentiment_view(self, mock_get_sentiments_for_sort_by_list, mock_get_initial_filter_values):
        """
        SentimentView should show a page for viewing sentiment letters, depending on filter_values
        """

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('sentiment_view'), follow=True)
        self.assertTemplateUsed(response, 'sentiment.html')

        self.assertEqual(mock_get_sentiments_for_sort_by_list.call_count, 1,
                         'SentimentView should call get_sentiments_for_sort_by_list()')

        expected = {'title': 'Letter sentiment', 'nbar': 'sentiment',
                    'filter_values': mock_get_initial_filter_values.return_value,
                    'show_search_text': 'true', 'show_sentiment': 'true'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "SentimentView context '{}' should be '{}'".format(key, expected[key]))
        self.assertIn('sort_by', response.context, "SentimentView context should contain 'sort_by'")


class LetterSentimentViewTestCase(TestCase):
    """
    Test LetterSentimentView
    """

    @patch('letters.views.letter_search.get_letter_sentiments', autospec=True)
    def test_letter_sentiment_view(self, mock_get_letter_sentiments):
        """
        If letter exists, LetterSentimentView should return response with list of sentiments

        For some reason, object_not_found() and get_highlighted_letter_sentiment() can't be successfully mocked,
        so actually call them
        """

        # If Letter with letter_id not found, LetterSentimentView should return object_not_found()
        response = self.client.get(reverse('letter_sentiment_view',
                                           kwargs={'letter_id': '1', 'sentiment_id': '1'}), follow=True)
        expected = {'title': 'Letter not found', 'object_id': '1', 'object_type': 'Letter'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "LetterSentimentView context '{}' should be '{}', if letter not found".format(key, expected[key]))

        # If Letter with letter_id found, LetterSentimentView should return get_highlighted_letter_sentiment()
        response = self.client.get(reverse('letter_sentiment_view',
                                           kwargs={'letter_id': LetterFactory().pk, 'sentiment_id': '1'}), follow=True)
        self.assertTemplateUsed(response, 'letter_sentiment.html')

        expected = {'title': 'Letter Sentiment', 'nbar': 'sentiment'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "LetterSentimentView context '{}' should be '{}', if letter found".format(key, expected[key]))


class GetHighlightedLetterSentimentTestCase(TestCase):
    """
    Test get_highlighted_letter_sentiment()
    """

    @patch('letters.views.highlight_letter_for_sentiment', autospec=True)
    def test_get_highlighted_letter_sentiment(self, mock_highlight_letter_for_sentiment):
        """
        get_highlighted_letter_sentiment() should show particular letter with sentiment highlights

        It's not a view, but it gets returned by the letter_sentiment_view
        """
        letter = LetterFactory()

        mock_highlight_letter_for_sentiment.return_value = [letter]

        title = 'Letter Sentiment'
        nbar = 'sentiment'
        sentiments = [('1', '0.1234')]

        request = RequestFactory().get(reverse('letter_sentiment_view', kwargs={'letter_id': '1', 'sentiment_id': '1'}),
                                       follow=True)
        response = get_highlighted_letter_sentiment(request, letter, sentiments)
        content = str(response.content)

        self.assertTrue(str(letter) in content)

        expected = [title, nbar, str(letter)]
        for item in expected:
            self.assertTrue(item in content,
                            "get_highlighted_letter_sentiment() response content should contain '{}'".format(item))
        for item in ['0.1234']:
            self.assertTrue(item in content,
                            "get_highlighted_letter_sentiment() response content should contain sentiment value".format(item))

        # If sentiment value is a list, all those values should end up in response
        mock_highlight_letter_for_sentiment.return_value = [letter, letter]
        sentiments = [('1', ['0.1234', '0.5678'])]

        request = RequestFactory().get(reverse('letter_sentiment_view', kwargs={'letter_id': '1', 'sentiment_id': '1'}),
                                       follow=True)
        response = get_highlighted_letter_sentiment(request, letter, sentiments)
        content = str(response.content)

        for item in ['0.1234', '0.5678']:
            self.assertTrue(item in content,
                            "get_highlighted_letter_sentiment() response content should contain sentiment value".format(item))


class HighlightLetterForSentimentTestCase(TestCase):
    """
    Test highlight_letter_for_sentiment()
    """

    @patch('letters.views.highlight_for_sentiment', autospec=True)
    @patch.object(Letter, 'body_as_text', autospec=True)
    def test_highlight_letter_for_sentiment(self, mock_body_as_text, mock_highlight_for_sentiment):
        """
        highlight_letter_for_sentiment() should call highlight_for_sentiment()
        for each of a letter's fields and return a copy of the letter with fields highlighted

        It returns a list, for some reason, even though only one sentiment_id is specified
        """

        mock_body_as_text.return_value = 'As this is the beginin of a new year I thought as I was a lone to night I ' \
                                         'would write you a few lines to let you know that we are not all ded yet.'
        letter = Letter(heading='Januery the 1st / 62',
                        greeting='Miss Evey',
                        closing='your friend as every',
                        signature='F.P. Black',
                        ps='p.s. remember me to enquirin friends')

        mock_highlight_for_sentiment.side_effect = [[letter.heading], [letter.greeting],
                                                    [mock_body_as_text.return_value], [letter.closing],
                                                    [letter.signature], [letter.ps]]

        result = highlight_letter_for_sentiment(letter, 1)

        self.assertEqual(mock_highlight_for_sentiment.call_args_list[0][0], (letter.heading, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(heading, sentiment_id)')
        self.assertEqual(mock_highlight_for_sentiment.call_args_list[1][0], (letter.greeting, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(greeting, sentiment_id)')
        self.assertEqual(mock_highlight_for_sentiment.call_args_list[2][0], (mock_body_as_text.return_value, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(body, sentiment_id)')
        self.assertEqual(mock_highlight_for_sentiment.call_args_list[3][0], (letter.closing, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(closing, sentiment_id)')
        self.assertEqual(mock_highlight_for_sentiment.call_args_list[4][0], (letter.signature, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(signature, sentiment_id)')
        self.assertEqual(mock_highlight_for_sentiment.call_args_list[5][0], (letter.ps, 1),
                         'highlight_letter_for_sentiment() should call highlight_for_sentiment(ps, sentiment_id)')

        self.assertEqual(letter.contents(), result[0].contents(),
                         'highlight_letter_for_sentiment() should return highlighted letter')


class TextSentimentViewTestCase(TestCase):
    """
    Test TextSentimentView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    def test_text_sentiment_view(self, mock_get_initial_filter_values):
        """
        TextSentimentView should return response containing filter values
        from get_initial_filter_values()
        """

        mock_get_initial_filter_values.return_value = 'initial filter values'

        response = self.client.get(reverse('text_sentiment_view'), follow=True)

        expected = {'title': 'Text sentiment', 'nbar': 'sentiment',
                    'filter_values': mock_get_initial_filter_values.return_value}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                             "TextSentimentView context '{}' should be '{}'".format(key, expected[key]))


class GetTextSentimentViewTestCase(SimpleTestCase):
    """
    Test GetTextSentimentView
    """

    @patch('letters.views.letters_filter.get_filter_values_from_request', autospec=True)
    @patch('letters.views.highlight_for_sentiment', autospec=True)
    @patch('letters.views.get_sentiment', autospec=True)
    @patch('letters.views.get_custom_sentiment_for_text', autospec=True)
    def test_get_text_sentiment_view(self, mock_get_custom_sentiment_for_text, mock_get_sentiment,
                                     mock_highlight_for_sentiment, mock_get_filter_values_from_request):

        # GET request should return HttpResponseNotAllowed
        response = self.client.get(reverse('get_text_sentiment'), follow=True)
        self.assertEqual(response.status_code, 405,
                         'Making a GET request to GetTextSentimentView should return HttpResponseNotAllowed')

        FilterValues = namedtuple('FilterValues',
                                  ['search_text', 'source_ids', 'writer_ids', 'start_date', 'end_date',
                                   'words',
                                   'sentiment_ids', 'sort_by'])
        filter_values = FilterValues(
            search_text='search_text',
            source_ids=[1, 2, 3],
            writer_ids=[1, 2, 3],
            start_date=['1862-01-01'],
            end_date=['1862-12-31'],
            words=['&', 'and'],
            sentiment_ids=[0, 1, 2],
            sort_by='sort_by'
        )
        mock_get_filter_values_from_request.return_value = filter_values
        mock_highlight_for_sentiment.return_value = 'highlight for sentiment'
        mock_get_custom_sentiment_for_text.return_value = 'custom sentiment for text'

        # POST
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('get_text_sentiment'), follow=True)
        response = GetTextSentimentView().dispatch(request)

        # highlight_for_sentiment() should be called for each sentiment
        self.assertEqual(mock_highlight_for_sentiment.call_count, 3,
                         'GetTextSentimentView should call highlight_for_sentiment() for each sentiment')

        # get_sentiment() should be called for sentiment with id 0
        self.assertEqual(mock_get_sentiment.call_count, 1,
                         'GetTextSentimentView should call get_sentiment() for sentiment with id 0')

        # get_custom_sentiment_for_text() should be called for each sentiment with id != 0
        self.assertEqual(mock_get_custom_sentiment_for_text.call_count, 2,
                         'GetTextSentimentView should call get_custom_sentiment_for_text() for sentiments with id != 0')

        content = json.loads(response.content.decode('utf-8'))
        self.assertTrue(mock_get_custom_sentiment_for_text.return_value in content['sentiments'],
                        "GetTextSentimentView should return custom sentiment in response content['sentiments']")


class HighlightForSentimentTestCase(SimpleTestCase):
    """
    Test highlight_for_sentiment()
    """


    @patch('letters.views.highlight_text_for_sentiment')
    @patch('letters.views.highlight_for_custom_sentiment')
    def test_highlight_for_sentiment(self, mock_highlight_for_custom_sentiment, mock_highlight_text_for_sentiment):
        """
        highlight_for_sentiment(text, sentiment_id) should return text highlighted with
        highlight_text_for_sentiment() if sentiment_id is 0
        Otherwise it should return text highlighted with highlight_for_custom_sentiment()
        """

        text = 'Hamburger kevin turducken'

        # highlight_for_sentiment(text, sentiment_id) should return text highlighted with
        # highlight_text_for_sentiment() if sentiment_id is 0
        highlight_for_sentiment(text, 0)

        args, kwargs = mock_highlight_text_for_sentiment.call_args
        self.assertEqual(args[0], text,
                    'highlight_for_sentiment() should call highlight_text_for_sentiment() if sentiment_id is 0')
        self.assertEqual(mock_highlight_for_custom_sentiment.call_count, 0,
                    "highlight_for_sentiment() shouldn't call highlight_for_custom_sentiment() if sentiment_id is 0")
        mock_highlight_text_for_sentiment.reset_mock()

        # highlight_for_sentiment(text, sentiment_id) should return text highlighted with
        # highlight_for_custom_sentiment() if sentiment_id is not 0
        highlight_for_sentiment(text, 1)

        args, kwargs = mock_highlight_for_custom_sentiment.call_args
        self.assertEqual(args[0], text,
                    "highlight_for_sentiment() should call highlight_for_custom_sentiment() if sentiment_id isn't 0")
        self.assertEqual(mock_highlight_text_for_sentiment.call_count, 0,
                    "highlight_for_sentiment() shouldn't call mock_highlight_text_for_sentiment() if sentiment_id isn't 0")
        mock_highlight_for_custom_sentiment.reset_mock()


class SearchViewTestCase(TestCase):
    """
    Test SearchView
    """

    @patch('letters.views.letter_search.do_letter_search')
    def test_search_view(self, mock_do_letter_search):
        """
        SearchView should return list of letters containing search text
        """

        # GET request should return HttpResponseNotAllowed
        response = self.client.get(reverse('search'), follow=True)
        self.assertEqual(response.status_code, 405,
                         'Making a GET request to SearchView should return HttpResponseNotAllowed')

        letter = LetterFactory()

        ES_Result = collections.namedtuple('ES_Result', ['search_results', 'total', 'pages'])
        search_results = [(letter, 'highlight', [('1', 'sentiment')], 'score')]
        es_result = ES_Result(search_results=search_results, total=42, pages=4)

        mock_do_letter_search.return_value = es_result

        # POST
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('search'), follow=True)

        # If search_text is supplied, the size passed to do_letter_search() should be 5
        request.POST = {'page_number': '1', 'search_text': 'Bacon ipsum dolor amet ball tip salami kielbasa'}
        SearchView().dispatch(request)

        args, kwargs = mock_do_letter_search.call_args
        self.assertEqual(args, (request, 5, 1),
                         'If search_text supplied to SearchView, the size passed to do_letter_search() should be 5')
        mock_do_letter_search.reset_mock()

        # If search_text not supplied, the size passed to do_letter_search() should be 10
        request.POST = {'page_number': '1'}
        response = SearchView().dispatch(request)

        args, kwargs = mock_do_letter_search.call_args
        self.assertEqual(args, (request, 10, 1),
                         'If search_text not supplied to SearchView, the size passed to do_letter_search() should be 10')
        mock_do_letter_search.reset_mock()

        # response content['pages'] should contain do_letter_search() result.pages
        # and response content['letters'] should contain letter from do_letter_search() result.search_results
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['pages'], mock_do_letter_search.return_value.pages,
                        "SearchView response content['pages'] should contain do_letter_search() result.pages")
        self.assertTrue(str(letter.writer) in content['letters'],
                        "SearchView response content['letters'] should contain letter found by do_letter_search()")

        # If page_number isn't 0, response content['pagination'] should be empty string
        self.assertEqual(content['pagination'], '',
                        "SearchView response content['pagination'] should be empty string if page_number isn't 0")

        # If page_number is 0, response content['pagination'] shouldn't be empty string
        request.POST = {'page_number': '0'}
        response = SearchView().dispatch(request)
        content = json.loads(response.content.decode('utf-8'))
        self.assertNotEqual(content['pagination'], '',
                            "SearchView response content['pagination'] shouldn't be empty string if page_number is 0")


class LetterDetailViewTestCase(TestCase):
    """
    Test LetterDetailView
    """

    def test_letter_detail_view(self):
        """
        LetterDetailView should call show_letter_content() if letter with id found
        """

        # If Letter with letter_id not found, LetterDetailView should return object not found
        response = self.client.get(reverse('letter_detail', kwargs={'pk': '1'}), follow=True)

        expected = {'title': 'Letter not found', 'object_id': '1', 'object_type': 'Letter'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "LetterDetailView context '{}' should be '{}', if letter not found".format(key, expected[key]))

        # If Letter with letter_id found, LetterDetailView should return show_letter_content()
        response = self.client.get(reverse('letter_detail', kwargs={'pk': LetterFactory().pk}), follow=True)
        self.assertTemplateUsed(response, 'letter.html')

        expected = {'title': 'Letter', 'nbar': 'letters_view'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "LetterDetailView context '{}' should be '{}', if letter found".format(key, expected[key]))


class ShowLetterContentTestCase(TestCase):
    """
    Test show_letter_content()
    """

    def test_show_letter_content(self):
        """
        show_letter_content(request, letter, title, nbar) should return rendered html
        showing content of letter
        """

        letter = LetterFactory()

        request = RequestFactory()
        response = show_letter_content(request, letter, title='The Title', nbar='nbar')
        content = str(response.content)

        self.assertTrue('<title>The Title</title>' in content,
                        'show_letter_content() response content should contain title')
        self.assertTrue(str(letter) in content,
                        'show_letter_content() response content should contain str(letter)')


class ExportCsvTestCase(TestCase):
    """
    Test export_csv()
    """

    @patch('io.StringIO', autospec=True)
    @patch('csv.writer', autospec=True)
    @patch.object(Letter, 'sort_date', autospec=True)
    @patch.object(Correspondent, 'to_export_string', autospec=True)
    @patch.object(Letter, 'contents', autospec=True)
    def test_export_csv(self, mock_letter_contents, mock_correspondent_to_export_string, mock_sort_date,
                        mock_csv_writer, mock_StringIO):
        """
        export_csv(letters) should write content of letters to a csv file and return it in a response
        """

        response = export_csv([LetterFactory()])

        self.assertEqual(mock_csv_writer.call_count, 1, 'export_csv() should call csv.writer()')
        self.assertEqual(mock_sort_date.call_count, 1, 'export_csv() should call Letter.sort_date()')
        self.assertEqual(mock_correspondent_to_export_string.call_count, 2,
                         'export_csv() should call Correspondent.to_export_string() twice')
        self.assertEqual(mock_letter_contents.call_count, 1, 'export_csv() should call Letter.contents()')

        self.assertEqual(response['content-type'],
                         'text/csv', "export_csv() should return response with content_type 'text/csv'")


class ExportTextTestCase(TestCase):
    """
    Test export_text()
    """

    @patch('letters.views.get_letter_export_text', autospec=True)
    def test_export_text(self, mock_get_letter_export_text):
        """
        export_text() should write content of letters to a csv file and return it in a response
        """

        letter = LetterFactory()

        response = export_text([letter])

        args, kwargs = mock_get_letter_export_text.call_args
        self.assertEqual(args[0], letter,
                         'export_text(letters) should call get_letter_export_text(letter for each letter)')

        self.assertEqual(type(response), HttpResponse, 'export_text() should return HttpResponse')
        self.assertEqual(response['content-type'],
                         'text/plain', "export_text() should return response with content_type 'text/plain'")


class GetLetterExportTextTestCase(TestCase):
    """
    Test get_letter_export_text()
    """

    @patch.object(Letter, 'index_date', autospec=True)
    @patch.object(Correspondent, 'to_export_string', autospec=True)
    @patch.object(Letter, 'contents', autospec=True)
    def test_get_letter_export_text(self, mock_letter_contents, mock_correspondent_to_export_string, mock_index_date):
        """
        get_letter_export_text() should return formatted string
        with letter date, writer, recipient, and contents
        """

        mock_index_date.return_value = '1862-01-02'
        mock_correspondent_to_export_string.return_value = 'Correspondent'
        mock_letter_contents.return_value = 'I thought as I was a lone to night I would write you a few lines to let ' \
                                            'you know that we are not all ded yet.'

        result = get_letter_export_text(LetterFactory())
        self.assertTrue(mock_index_date.return_value in result,
                        'get_letter_export_text() return value should contain letter.index_date()')
        self.assertTrue(mock_correspondent_to_export_string.return_value in result,
                        'get_letter_export_text() return value should contain writer and recipient')
        self.assertTrue(mock_letter_contents.return_value in result,
                        'get_letter_export_text() return value should contain letter.contents()')#


class RandomLetterViewTestCase(TestCase):
    """
    Test RandomLetterView
    """

    def test_random_letter_view(self):
        """
        RandomLetterView should retrieve a letter with a random index
        between 1 and total Letter objects.count() - 1
        """

        # If only no Letters, RandomLetterView should return object not found page
        response = self.client.get(reverse('random_letter'), follow=True)

        self.assertTemplateUsed(response, 'obj_not_found.html')
        self.assertTrue('Letter not found' in str(response.context),
                         'If no Letters, RandomLetterView should return object not found page')

        # If one letter, random_letter() should return that one
        letter = LetterFactory()

        response = self.client.get(reverse('random_letter'), follow=True)
        self.assertIn('Random letter', str(response.content),
                        "Random letter page should be shown if there's at least one letter in database")
        self.assertIn(str(letter), str(response.content),
                      'If one Letter, RandomLetterView should return that letter')

        # If more than one letter, RandomLetterView should return one of them
        letter2 = LetterFactory()

        with patch('random.randint', autospec=True) as mock_randint:
            mock_randint.return_value = 1

            response = self.client.get(reverse('random_letter'), follow=True)

            self.assertIn('Random letter', str(response.content),
                          "If more than one Letter, RandomLetterView should return page title 'Random letter")
            self.assertIn(str(letter2), str(response.content),
                          "If more than one Letter, RandomLetterView should return randomly chosen letter")


class PPlaceListViewTestCase(TestCase):
    """
    Test PlaceListView
    """

    @patch('letters.views.letters_filter.get_initial_filter_values', autospec=True)
    @patch('letters.views.render_to_string', autospec=True)
    def test_place_list_view(self, mock_render_to_string, mock_get_initial_filter_values):
        """
        PlaceListView should show a set of initial values and the first 100 Places
        """

        mock_get_initial_filter_values.return_value = 'initial filter values'

        barbecue = PlaceFactory(name='Barbecue', state='North Carolina', point=Point(0, 0))
        bacon_level = PlaceFactory(name='Bacon Level', state='Alabama')

        response = self.client.get(reverse('place_list'), follow=True)
        args, kwargs = mock_render_to_string.call_args
        self.assertTrue(barbecue in args[1]['places'],
                        'PlaceListView should call render_to_string() with places that have coordinates in args')
        self.assertFalse(bacon_level in args[1]['places'],
                        'PlaceListView should call render_to_string() without places that have no coordinates in args')

        content = str(response.content)
        self.assertTrue('<title>Places</title>' in content, "PlaceListView should return page with 'Places' as title")


class PlaceSearchViewTestCase(SimpleTestCase):
    """
    Test PlaceSearchView
    """

    @patch('letters.views.letter_search.do_letter_search')
    @patch('letters.views.render_to_string', autospec=True)
    def test_place_search_view(self, mock_render_to_string, mock_do_letter_search):
        # GET request should return HttpResponseNotAllowed
        response = self.client.get(reverse('place_search'), follow=True)
        self.assertEqual(response.status_code, 405,
                         'Making a GET request to PlaceSearchView should return HttpResponseNotAllowed')

        mock_render_to_string.return_value = 'render to string'

        # POST
        # For some reason, it's impossible to request a POST request via the Django test client,
        # so manually create one and call the view directly
        request = RequestFactory().post(reverse('place_search'))

        response = PlaceSearchView().dispatch(request)

        self.assertEqual(mock_do_letter_search.call_count, 1, 'PlaceSearchView should call do_letter_search()')
        self.assertEqual(mock_render_to_string.call_count, 1, 'PlaceSearchView should call render_to_string()')

        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['map'], mock_render_to_string.return_value,
                         "PlaceSearchView should return response containing 'map'")


class PlaceDetailViewTestCase(TestCase):
    """
    Test PlaceDetailView
    """

    def test_place_detail_view(self):
        """
        PlaceDetailView should return rendered html if Place with id found
        Otherwise it should return object not found
        """

        response = self.client.get(reverse('place_detail', kwargs={'pk': '1'}), follow=True)

        expected = {'title': 'Place not found', 'object_id': '1', 'object_type': 'Place'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "PlaceDetailView context '{}' should be '{}', if place not found".format(key, expected[key]))


        # If Place with pk found, PlaceDetailView should return render()
        response = self.client.get(reverse('place_detail', kwargs={'pk': PlaceFactory().pk}), follow=True)
        self.assertTemplateUsed(response, 'place.html')

        expected = {'title': 'Place', 'nbar': 'places'}
        for key in expected.keys():
            self.assertEqual(response.context[key], expected[key],
                "PlaceDetailView context '{}' should be '{}', if letter found".format(key, expected[key]))
