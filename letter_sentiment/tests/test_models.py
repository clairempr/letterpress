from unittest.mock import patch

from django.test import TestCase

from letter_sentiment.models import analyze_text, Term
from letter_sentiment.tests.factories import CustomSentimentFactory, TermFactory


class CustomSentimentTestCase(TestCase):
    """
    Test CustomSentiment model
    """

    def test__str__(self):
        """
        __str__() should return CustomSentiment.name
        """

        custom_sentiment = CustomSentimentFactory(name='Hipster')
        self.assertEqual(str(custom_sentiment), custom_sentiment.name,
                         '__str__() should return CustomSentiment.name')

    def test_get_terms(self):
        """
        get_terms() should return CustomSentiment's terms
        """

        dreamcatcher_term = TermFactory(text='slow-carb dreamcatcher')
        taxidermy_term = TermFactory(text='taxidermy kickstarter')

        custom_sentiment = CustomSentimentFactory(name='Hipster')
        custom_sentiment.terms.add(dreamcatcher_term, taxidermy_term)

        self.assertEqual(set(custom_sentiment.get_terms()), set([dreamcatcher_term, taxidermy_term]),
                         "get_terms() should return CustomSentiment's terms")


class TermTestCase(TestCase):
    """
    Test Term model
    """

    def test__str__(self):
        """
        __str__() should return Term.text
        """

        text = 'freegan vaporware'

        term = TermFactory(text=text)
        self.assertEqual(str(term), text, '__str_() should return Term.text')

    def test_number_of_words(self):
        """
        number_of_words() should return number of words in Term.text
        """

        term = TermFactory(text='offal mustache')
        self.assertEqual(term.number_of_words(), 2, 'number_of_words() should return number of words in Term.text')

    @patch('letter_sentiment.models.analyze_text', autospec=True)
    def test_save(self, mock_analyze_text):
        """
        If Term.text has changed, it should be analyzed again

        Can't figure out to reference to __original_text in unit test
        """

        text = 'gluten-free pabst'

        mock_analyze_text.return_value = text

        # Test with actual Term because analyze_text() is mocked in TermFactory object creation
        term = Term.objects.create(text=text, analyzed_text=text,
                                   custom_sentiment=CustomSentimentFactory())
        self.assertEqual(mock_analyze_text.call_count, 0,
                         "If Term.text hasn't changed, it shouldn't be analyzed again")

        term.text = 'gluten pabst'
        term.save()
        self.assertEqual(mock_analyze_text.call_count, 1,
                         'If Term.text has changed, it should be analyzed again')

    @patch('letter_sentiment.models.analyze_term', autospec=True)
    def test_analyze_text(self, mock_analyze_term):
        """
        analyze_text() should call analyze_term() for text, using string_sentiment_analyzer
        """

        text = 'chartreuse tote bag'
        analyze_text(text)

        args, kwargs = mock_analyze_term.call_args
        self.assertEqual(args[0], text, 'analyze_text() should call analyze_term() for text')
        self.assertEqual(kwargs.get('analyzer'), 'string_sentiment_analyzer',
                         'analyze_text() should call analyze_term() with string_sentiment_analyzer')
