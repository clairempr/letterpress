from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from letters.sort_by import get_selected_sentiment_id, get_sentiments_for_sort_by_list, SENTIMENT
from letter_sentiment.tests.factories import CustomSentimentFactory


class GetSelectedSentimentIdTestCase(SimpleTestCase):
    """
    get_selected_sentiment_id(filter_value) should remove leading SENTIMENT from filter_value
    and return the remaining sentiment_id as an int
    """

    def test_get_selected_sentiment_id(self):
        # If filter_value doesn't start with SENTIMENT, get_selected_sentiment_id(filter_value) should return 0
        self.assertEqual(
            get_selected_sentiment_id('test'), 0,
            "If filter_value doesn't start with SENTIMENT, get_selected_sentiment_id(filter_value) should return 0"
        )

        # If filter_value starts with SENTIMENT, get_selected_sentiment_id(filter_value) should return sentiment_id
        filter_value = SENTIMENT + '5'
        self.assertEqual(
            get_selected_sentiment_id(filter_value), 5,
            'If filter_value starts with SENTIMENT, get_selected_sentiment_id(filter_value) should return sentiment_id'
        )


class GetSentimentsForSortByListTestCase(TestCase):
    """
    get_sentiments_for_sort_by_list() should return a list of tuples with sentiment id and name of custom sentiments
    """

    @patch('letters.sort_by.get_custom_sentiments', autospec=True)
    def test_get_sentiments_for_sort_by_list(self, mock_get_custom_sentiments):
        hipster_sentiment = CustomSentimentFactory(name='Hipster')
        ponies_sentiment = CustomSentimentFactory(name='OMG Ponies!!!')

        mock_get_custom_sentiments.return_value = [hipster_sentiment, ponies_sentiment]

        custom_sentiments = get_sentiments_for_sort_by_list()
        for sentiment in [hipster_sentiment, ponies_sentiment]:
            self.assertIn((SENTIMENT + str(sentiment.id), sentiment.name), custom_sentiments,
                          'get_sentiments_for_sort_by_list() should return tuples of SENTIMENT id, sentiment name')
