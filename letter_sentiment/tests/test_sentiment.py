from unittest.mock import patch
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as vaderSentiment

from django.test import SimpleTestCase

from letter_sentiment.sentiment import do_sentiment_highlight, format_sentiment, get_sentiment, get_textblob_polarity, \
    get_vadersentiment_polarity, highlight_text_for_sentiment, sentiment_to_string


class DoSentimentHighlight(SimpleTestCase):
    """
    do_sentiment_highlight(text, polarity) should wrap the text in a <span>
    with css class that depends on polarity
    """

    def test_do_sentiment_highlight(self):
        positive_class = 'sentiment-highlight-pos'
        slightly_positive_class = 'sentiment-highlight-sorta-pos'
        slightly_negative_class = 'sentiment-highlight-sorta-neg'
        negative_class = 'sentiment-highlight-neg'

        text = 'goth paleo coloring book'

        # polarity < -0.5 should be 'sentiment-highlight-neg'
        self.assertTrue(
            negative_class in do_sentiment_highlight(text, -0.55),
            "do_sentiment_highlight() should return span with class '{}' when polarity is -0.55".format(negative_class)
        )

        # polarity >= -0.5 and < -0.2 should be 'sentiment-highlight-sorta-neg'
        for polarity in [-0.5, -0.3]:
            self.assertTrue(slightly_negative_class in do_sentiment_highlight(text, polarity),
                            "do_sentiment_highlight() should return span with class '{}' when polarity is {}".format(
                                slightly_negative_class, polarity))
        # polarity >= -0.2 and < 0.2 shouldn't be wrapped in a span
        for polarity in [-0.2, 0]:
            self.assertFalse(
                '<span>' in do_sentiment_highlight(text, polarity),
                "do_sentiment_highlight() shouldn't wrap text in a <span> when polarity is {}".format(polarity)
            )
        for polarity in [0.2, 0.3]:
            self.assertTrue(slightly_positive_class in do_sentiment_highlight(text, polarity),
                            "do_sentiment_highlight() should return span with class '{}' when polarity is {}".format(
                                slightly_positive_class, polarity))
        # polarity >= 0.5 should be 'sentiment-highlight-pos'
        for polarity in [0.5, 0.6]:
            self.assertTrue(positive_class in do_sentiment_highlight(text, polarity),
                            "sentiment_to_string() should return '{}' when polarity is {}".format(positive_class,
                                                                                                  polarity))


class FormatSentimentTestCase(SimpleTestCase):
    """
    format_sentiment(sentiment, polarity) should return a string containing sentiment name
    and float-formatted polarity
    """

    def test_format_sentiment(self):
        sentiment = 'Hipster'
        polarity = .75

        result = format_sentiment(sentiment, polarity)

        self.assertTrue(sentiment in result,
                        'format_sentiment() should return string containing sentiment name')
        self.assertTrue('0.750' in result,
                        'format_sentiment() should return string containing float-formatted polarity')


class GetSentimentTestCase(SimpleTestCase):
    """
    get_sentiment() should analyze sentiment of text_to_analyze with both vaderSentiment and TextBlob,
    and return the polarity of each
    """

    @patch('letter_sentiment.sentiment.get_textblob_polarity', autospec=True)
    @patch('letter_sentiment.sentiment.format_sentiment', autospec=True)
    @patch('letter_sentiment.sentiment.sentiment_to_string', autospec=True)
    @patch('letter_sentiment.sentiment.get_vadersentiment_polarity', autospec=True)
    def test_get_sentiment(self, mock_get_vadersentiment_polarity, mock_sentiment_to_string, mock_format_sentiment,
                           mock_get_textblob_polarity):
        mock_get_textblob_polarity.return_value = -0.7
        mock_get_vadersentiment_polarity.return_value = -0.65

        text = 'Tis difficult to sympathize with the bereft untill we are ourselves bereaved'
        result = get_sentiment(text)

        # get_textblob_polarity() should be called
        args, kwargs = mock_get_textblob_polarity.call_args
        self.assertEqual(args[0], text, 'get_sentiment() should call get_textblob_polarity(text_to_analyze)')

        # get_vadersentiment_polarity() should be called
        args, kwargs = mock_get_vadersentiment_polarity.call_args
        self.assertEqual(args[0], text, 'get_sentiment() should call get_vadersentiment_polarity(text_to_analyze)')

        # format_sentiment() should be called twice
        self.assertEqual(mock_format_sentiment.call_count, 2, 'get_sentiment() should call format_sentiment() twice')

        # sentiment_to_string() should be called twice
        self.assertEqual(mock_sentiment_to_string.call_count, 2,
                         'get_sentiment() should call sentiment_to_string() twice')

        # return value should contain 'TextBlob' and 'Vader'
        text_blob, vader = result
        self.assertTrue('TextBlob' in text_blob, "get_sentiment() should return value that contains ''TextBlob''")
        self.assertTrue('Vader' in vader, "get_sentiment() should return value that contains ''Vader''")


class GetTextblobPolarityTestCase(SimpleTestCase):
    """
    get_textblob_polarity() should analyze text with TextBlob and return the polarity
    """

    def test_get_textblob_polarity(self):
        """
        Couldn't figure out how to mock TextBlob successfully,
        so just test for expected values based on text
        """
        result = get_textblob_polarity('This is terrific')
        self.assertGreaterEqual(result, 0, "get_textblob_polarity() should return polarity > 0 for 'This is terrific'")

        result = get_textblob_polarity('This is neutral')
        self.assertEqual(result, 0,
                         "get_textblob_polarity() should return polarity 0 for 'This is neutral'")

        result = get_textblob_polarity('This is awful')
        self.assertLessEqual(result, 0,
                             "get_textblob_polarity() should return polarity <>> 0 for 'This is awful'")


class GetVadersentimentPolarityTestCase(SimpleTestCase):
    """
    get_vadersentiment_polarity() should get the positive and negative scores of the vaderSentiment analyzer
    and return positive score minus negative score
    """

    @patch.object(vaderSentiment, 'polarity_scores', autospec=True)
    def test_get_vadersentiment_polarity(self, mock_vaderSentiment):
        mock_vaderSentiment.return_value = {'pos': 0.4, 'neg': 0.6}
        text = "90's mumblecore squid"

        result = get_vadersentiment_polarity(text)
        # In this case, the polarity returned is -0.19999999999999996, so use assertAlmostEqual
        self.assertAlmostEqual(result, -0.2)


class HighlightTextForSentimentTestCase(SimpleTestCase):
    """
    highlight_text_for_sentiment() should get highlights for both TextBlob sentiment and vaderSentiment
    """
    @patch('letter_sentiment.sentiment.get_vadersentiment_polarity', autospec=True)
    @patch('letter_sentiment.sentiment.do_sentiment_highlight', autospec=True)
    def test_highlight_text_for_sentiment(self, mock_do_sentiment_highlight, mock_get_vadersentiment_polarity):
        textblob_highlight = 'TextBlob sentiment highlight'
        vader_highlight = 'vaderSentiment highlight'
        mock_do_sentiment_highlight.side_effect = [textblob_highlight, vader_highlight]

        # Couldn't figure out how to mock TextBlob successfully, so just use the real thing
        text = 'seitan viral messenger bag'

        result = highlight_text_for_sentiment(text)

        args, kwargs = mock_get_vadersentiment_polarity.call_args
        self.assertEqual(args[0], text, 'highlight_text_for_sentiment() should call get_vadersentiment_polarity()')
        self.assertEqual(mock_do_sentiment_highlight.call_count, 2,
                         'highlight_text_for_sentiment() should call do_sentiment_highlight() at least twice')

        highlighted_textblob, highlighted_vader = result
        self.assertTrue(textblob_highlight in highlighted_textblob,
                        'highlight_text_for_sentiment() should return text highlighted with TextBlob sentiment')
        self.assertTrue(vader_highlight in highlighted_vader,
                        'highlight_text_for_sentiment() should return text highlighted with vaderSentiment')


class SentimentToStringTestCase(SimpleTestCase):
    """
    sentiment_to_string(polarity) should return a string corresponding to polarity
    """

    def test_sentiment_to_string(self):
        positive = 'positive'
        slightly_positive = 'slightly positive'
        neutral = 'neutral'
        slightly_negative = 'slightly negative'
        negative = 'negative'

        # polarity < -0.5 should be 'negative'
        self.assertEqual(sentiment_to_string(-0.55),
                         negative,
                         "sentiment_to_string() should return '{}' when polarity is -0.55".format(negative))
        # polarity >= -0.5 and < -0.2 should be 'slightly negative'
        for polarity in [-0.5, -0.3]:
            self.assertEqual(sentiment_to_string(polarity),
                             slightly_negative,
                             "sentiment_to_string() should return '{}' when polarity is {}".format(slightly_negative,
                                                                                                   polarity))
        # polarity >= -0.2 and < 0.2 should be 'neutral'
        for polarity in [-0.2, 0]:
            self.assertEqual(sentiment_to_string(polarity),
                             neutral,
                             "sentiment_to_string() should return '{}' when polarity is {}".format(neutral, polarity))
        # polarity >= 0.2 and < 0.5 should be 'slightly positive'
        for polarity in [0.2, 0.3]:
            self.assertEqual(sentiment_to_string(polarity),
                             slightly_positive,
                             "sentiment_to_string() should return '{}' when polarity is {}".format(slightly_positive,
                                                                                                   polarity))
        # polarity >= 0.5 should be 'positive'
        for polarity in [0.5, 0.6]:
            self.assertEqual(sentiment_to_string(polarity),
                             positive,
                             "sentiment_to_string() should return '{}' when polarity is {}".format(positive, polarity))
