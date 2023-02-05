from django_date_extensions.fields import ApproximateDate
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from letters import es_settings
from letters.models import Letter
from letters.tests.factories import LetterFactory
from letter_sentiment.elasticsearch import calculate_custom_sentiment, get_custom_sentiment_query, \
    get_sentiment_function_score_query, get_sentiment_match_query
from letter_sentiment.tests.factories import CustomSentimentFactory, TermFactory


class CalculateCustomSentimentTestCase(TestCase):
    """
    calculate_custom_sentiment() should retrieve a custom sentiment query,
    do a search with Elasticsearch and return the score from the first (only) hit
    """

    # We don't want to be messing with the real Elasticsearch index, in case something goes wrong
    # with mocking
    @patch('letters.models.Letter._meta.es_index_name', 'letterpress_test')
    @patch('letter_sentiment.elasticsearch.get_custom_sentiment_query', autospec=True)
    @patch('letter_sentiment.elasticsearch.do_es_search', autospec=True)
    def test_calculate_custom_sentiment(self, mock_do_es_search, mock_get_custom_sentiment_query):
        mock_get_custom_sentiment_query.return_value = {'find me the thing'}
        expected_result = 1
        mock_do_es_search.return_value = {'hits': {'hits': [{'_score': expected_result}]}}

        result = calculate_custom_sentiment(1, 2)

        # get_custom_sentiment_query() should get called
        args, kwargs = mock_get_custom_sentiment_query.call_args
        self.assertEqual(
            args, (1, 2),
            'calculate_custom_sentiment() should call get_custom_sentiment_query(letter_id, sentiment_id)'
        )

        # do_es_search() should get called
        args, kwargs = mock_do_es_search.call_args
        self.assertEqual(kwargs['index'], [Letter._meta.es_index_name],
                         'calculate_custom_sentiment() should call do_es_search() with index as kwarg')
        self.assertEqual(kwargs['query'], mock_get_custom_sentiment_query.return_value,
                         'calculate_custom_sentiment() should call do_es_search() with query as kwarg')

        # Return value should be score from hits
        self.assertEqual(result, expected_result,
                         'calculate_custom_sentiment() should return Elasticsearch score from hits')

        # If no hits, return value should be 0
        mock_do_es_search.return_value = {}
        result = calculate_custom_sentiment(1, 2)
        self.assertEqual(result, 0,
                         'calculate_custom_sentiment() should return 0 if no Elasticsearch hits')

    # We don't want to be messing with the real Elasticsearch index
    @patch('letters.models.Letter._meta.es_index_name', 'letterpress_test')
    def test_calculate_custom_sentiment_without_mocks(self):
        """
        Haven't yet figured out why Elasticsearch doesn't deliver the same score in test as in
        prod, so for now just make sure it doesn't cause an error
        """
        sentiment = CustomSentimentFactory(name='OMG Ponies!', max_weight=2)
        TermFactory(text='pony', weight=2, custom_sentiment=sentiment)
        TermFactory(text='horse', weight=1, custom_sentiment=sentiment)

        letter = LetterFactory(date=ApproximateDate(1970, 1, 1),
                               body='Look at the horse. Look at the pony.')

        # Make sure there's not already an indexed document with the same Id
        # because it might not have gotten cleaned up properly after a previous test
        if es_settings.ES_CLIENT.exists(index=[Letter._meta.es_index_name],
                                        id=letter.pk):
            letter.delete_from_elasticsearch(pk=letter.pk)
        letter.create_or_update_in_elasticsearch(is_new=None)

        calculate_custom_sentiment(letter_id=letter.id, sentiment_id=sentiment.id)

        letter.delete_from_elasticsearch(pk=letter.pk)


class GetCustomSentimentQuery(SimpleTestCase):
    """
    Should get the query with all the custom sentiment terms in it
    """

    @patch('letter_sentiment.elasticsearch.get_sentiment_match_query', autospec=True)
    @patch('letter_sentiment.elasticsearch.get_sentiment_function_score_query', autospec=True)
    def test_get_custom_sentiment_query(self, mock_get_sentiment_function_score_query, mock_get_sentiment_match_query):
        query = get_custom_sentiment_query(letter_id=1, sentiment_id=2)

        # get_custom_sentiment_query() should call get_sentiment_match_query(sentiment_id)
        args, kwargs = mock_get_sentiment_match_query.call_args
        self.assertEqual(args[0], 2,
                         'get_custom_sentiment_query() should call get_sentiment_match_query(sentiment_id)')

        # get_custom_sentiment_query() should call get_sentiment_function_score_query
        self.assertEqual(mock_get_sentiment_function_score_query.call_count, 1,
                         'get_custom_sentiment_query() should call get_sentiment_function_score_query()')

        # get_custom_sentiment_query() should return the query
        for key in ['function_score']:
            self.assertIn(key, query.keys(), 'get_custom_sentiment_query() should return query with key {}'.format(key))


class GetSentimentFunctionScoreQuery(SimpleTestCase):
    """
    Should return dict with 'query' and 'script_score'
    'bool_query' should be inside of 'query'
    """

    def test_get_sentiment_function_score_query(self,):
        query = get_sentiment_function_score_query({'bool_query'})

        # get_sentiment_function_score_query() should return dict with 'query' and 'script_score'
        for key in ['query', 'script_score']:
            self.assertIn(key, query.keys(),
                          'get_sentiment_function_score_query() should return {}'.format(key))
        # get_sentiment_function_score_query() should return dict with 'bool_query' inside of 'query'
        self.assertIn('bool', query['query'],
                      "get_sentiment_function_score_query() should return dict with 'bool' inside of 'query'")


class GetSentimentMatchQuery(TestCase):
    """
    Should return a list of term match queries
    """

    def test_get_sentiment_match_query(self):
        # get_sentiment_match_query() should return empty list if CustomSentiment not found
        sentiment_match_query = get_sentiment_match_query(1)
        self.assertEqual(sentiment_match_query, [],
                         'get_sentiment_match_query() should return empty list if CustomSentiment not found')

        # if CustomSentiment is found, get_sentiment_match_query() should return list of dicts with key 'match_phrase'
        sentiment = CustomSentimentFactory(max_weight=1)
        TermFactory(text='pitchfork tattooed bicycle', analyzed_text='pitchfork tattooed bicycle',
                    custom_sentiment=sentiment)

        sentiment_match_query = get_sentiment_match_query(sentiment.id)
        for query in sentiment_match_query:
            self.assertIn(
                'match_phrase', query,
                "get_sentiment_match_query() should return dict list with key 'match_phrase' if CustomSentiment found"
            )
