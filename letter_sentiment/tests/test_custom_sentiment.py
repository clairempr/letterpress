import copy
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from letter_sentiment.custom_sentiment import get_analyzed_custom_sentiment_terms, get_custom_sentiment, \
    get_custom_sentiment_for_letter, get_custom_sentiment_for_text, get_custom_sentiment_name, get_custom_sentiments, \
    get_token_offsets, highlight_for_custom_sentiment, sort_terms_by_number_of_words, update_tokens_in_termvector
from letter_sentiment.tests.factories import CustomSentimentFactory, TermFactory
from letters.elasticsearch import get_sentiment_termvector_for_text


class GetAnalyzedCustomSentimentTermsTestCase(TestCase):
    """
    get_analyzed_custom_sentiment_terms() should return a list of analyzed text
    for all of a CustomSentiment's terms
    """

    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment', autospec=True)
    def test_get_analyzed_custom_sentiment_terms(self, mock_get_custom_sentiment):
        custom_sentiment = CustomSentimentFactory(name='Hipster')

        TermFactory(text='hot chicken letterpress', analyzed_text='hot chicken letterpress',
                    custom_sentiment=custom_sentiment)
        TermFactory(text='banjo kitsch', analyzed_text='banjo kitsch',
                    custom_sentiment=custom_sentiment)
        TermFactory(text='gentrify taxidermy', analyzed_text='gentrify taxidermy',
                    custom_sentiment=custom_sentiment)

        # get_analyzed_custom_sentiment_terms() should return list of analyzed text
        # for custom sentiment's terms
        mock_get_custom_sentiment.return_value = custom_sentiment
        expected_list = ['hot chicken letterpress', 'banjo kitsch', 'gentrify taxidermy']
        self.assertEqual(set(get_analyzed_custom_sentiment_terms(1)), set(expected_list),
                        "get_analyzed_custom_sentiment_terms() should return list of CustomSentiment's analyzed text")

        # If no CustomSentiment found with that Id, get_analyzed_custom_sentiment_terms()
        # should return empty list
        mock_get_custom_sentiment.return_value = None
        self.assertEqual(get_analyzed_custom_sentiment_terms(1), [],
                        "get_analyzed_custom_sentiment_terms() should return empty list if CustomSentiment not found")


class GetCustomSentimentTestCase(TestCase):
    """
    get_custom_sentiment() should return CustomSentiment with given id if it exists
    Otherwise it should return None
    """

    def test_get_custom_sentiment(self):
        custom_sentiment = CustomSentimentFactory(name='OMG Ponies!')
        self.assertEqual(get_custom_sentiment(custom_sentiment.id), custom_sentiment,
                         'get_custom_sentiment() should return CustomSentiment with given id if it exists')

        self.assertIsNone(get_custom_sentiment(42),
                          'get_custom_sentiment() should return None if no CustomSentiment with given id exists')


class GetCustomSentimentForLetterTestCase(TestCase):
    """
    get_custom_sentiment_for_letter(letter_id, custom_sentiment_id) should return name of custom sentiment,
    along with calculated sentiment for letter
    """

    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment', autospec=True)
    @patch('letter_sentiment.custom_sentiment.calculate_custom_sentiment', autospec=True, return_value=0.5)
    @patch('letter_sentiment.custom_sentiment.format_sentiment', autospec=True, return_value='Sentiment (0.25)')
    def test_get_custom_sentiment_for_letter(self, mock_format_sentiment,
                                             mock_calculate_custom_sentiment,
                                             mock_get_custom_sentiment):
        custom_sentiment_name = 'OMG Ponies!'
        letter_id = 3

        # If no CustomSentiment found with custom_sentiment_id (get_custom_sentiment() returns None),
        # get_custom_sentiment_for_letter() should return 0
        mock_get_custom_sentiment.return_value = None

        self.assertEqual(get_custom_sentiment_for_letter(letter_id=letter_id, custom_sentiment_id=1), 0,
            'get_custom_sentiment_for_letter() should return 0 if no CustomSentiment found with custom_sentiment_id')

        # If CustomSentiment has no terms, get_custom_sentiment_for_letter() should return 0
        custom_sentiment = CustomSentimentFactory(name=custom_sentiment_name)
        mock_get_custom_sentiment.return_value = custom_sentiment

        self.assertEqual(get_custom_sentiment_for_letter(letter_id=letter_id, custom_sentiment_id=custom_sentiment.id),
                         0, 'get_custom_sentiment_for_letter() should return 0 if CustomSentiment has no terms')

        # calculate_custom_sentiment(letter_id, custom_sentiment_id) should be called
        TermFactory(text='horse', custom_sentiment=custom_sentiment)
        TermFactory(text='pony', custom_sentiment=custom_sentiment)
        mock_get_custom_sentiment.return_value = custom_sentiment

        custom_sentiment_for_letter = get_custom_sentiment_for_letter(letter_id=letter_id,
                                                                  custom_sentiment_id=custom_sentiment.id)
        args, kwargs = mock_calculate_custom_sentiment.call_args
        self.assertEqual(args, (letter_id, custom_sentiment.id),
            'get_custom_sentiment_for_letter() should call calculate_custom_sentiment(letter_id, custom_sentiment_id)')

        # format_sentiment(custom_sentiment.name, sentiment) should be called
        args, kwargs = mock_format_sentiment.call_args
        self.assertEqual(args, (custom_sentiment_name, mock_calculate_custom_sentiment.return_value),
                    'get_custom_sentiment_for_letter() should call format_sentiment(custom_sentiment.name, sentiment)')

        # get_custom_sentiment_for_letter() should return the value of format_sentiment()
        self.assertEqual(custom_sentiment_for_letter, mock_format_sentiment.return_value,
                         'get_custom_sentiment_for_letter() should return the value of format_sentiment()')


class GetCustomSentimentForTextTestCase(SimpleTestCase):
    """
    get_custom_sentiment_for_text() should temporarily index text as contents of letter,
    calculate custom sentiment for that letter, and return the sentiment
    """

    @patch('letter_sentiment.custom_sentiment.index_temp_document', autospec=True)
    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment_for_letter', autospec=True)
    @patch('letter_sentiment.custom_sentiment.delete_temp_document', autospec=True)
    def test_get_custom_sentiment_for_text(self, mock_delete_temp_document,
                                           mock_get_custom_sentiment_for_letter,
                                           mock_index_temp_document):
        mock_get_custom_sentiment_for_letter.return_value = 0.3

        text = 'Shopping you know is very dangerous'
        custom_sentiment_id = 1

        sentiment = get_custom_sentiment_for_text(text=text, custom_sentiment_id=custom_sentiment_id)

        # index_temp_document(text) should be called
        args, kwargs = mock_index_temp_document.call_args
        self.assertEqual(args[0], text,
                         'get_custom_sentiment_for_text() should call index_temp_document(text)')

        # get_custom_sentiment_for_letter('temp', custom_sentiment_id) should be called
        args, kwargs = mock_get_custom_sentiment_for_letter.call_args
        self.assertEqual(args, ('temp', custom_sentiment_id),
                         'get_custom_sentiment_for_text() should call get_custom_sentiment_for_letter(text, id)')

        # delete_temp_document() should be called
        self.assertEqual(mock_delete_temp_document.call_count, 1,
                         'get_custom_sentiment_for_text() should call delete_temp_document()')

        # get_custom_sentiment_for_text() should return the sentiment that was returned
        # from get_custom_sentiment_for_letter()
        self.assertEqual(sentiment, mock_get_custom_sentiment_for_letter.return_value,
                    'get_custom_sentiment_for_text() should return sentiment from get_custom_sentiment_for_letter()')


class GetCustomSentimentNameTestCase(TestCase):
    """
    get_custom_sentiment_name() should return the name of the CustomSentiment
    returned by get_custom_sentiment(), if there is one
    Otherwise it should return an empty string
    """

    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment', autospec=True)
    def test_get_custom_sentiment(self, mock_get_custom_sentiment):
        custom_sentiment_name = 'Hipster'
        custom_sentiment = CustomSentimentFactory(name=custom_sentiment_name)

        mock_get_custom_sentiment.return_value = custom_sentiment
        self.assertEqual(get_custom_sentiment_name(custom_sentiment.id), custom_sentiment.name,
                         'get_custom_sentiment_name() should return name of custom sentiment')

        mock_get_custom_sentiment.return_value = None
        self.assertEqual(get_custom_sentiment_name(42), '',
                         'get_custom_sentiment_name() should return empty string if custom sentiment not found')


class GetCustomSentimentsTestCase(TestCase):
    """
    get_custom_sentiments() should return all CustomSentiment objects
    Why did I write this?
    """

    def test_get_custom_sentiments(self):
        hipster_sentiment = CustomSentimentFactory(name='Hipster')
        pony_sentiment = CustomSentimentFactory(name='OMG Ponies!')

        self.assertEqual(set(get_custom_sentiments()), set([hipster_sentiment, pony_sentiment]))


class GetTokenOffsetsTestCase(SimpleTestCase):
    """
    get_token_offsets() should extract 'start_offset', 'end_offset', and 'position'
    from token dict and return them as a tuple (start_offset, end_offset, position)
    """

    def test_get_token_offsets(self):
        """
        If any of the keys aren't in token, those values should be returned as 0
        """

        start_offset = 1
        end_offset = 2
        position = 3

        # None present: tuple should be all zeroes
        self.assertEqual(get_token_offsets({}), (0, 0, 0),
                         'get_token_offsets() should return 0 for any keys not found in token')

        # 'start_offset' not present
        token = {'end_offset': end_offset, 'position': position}
        self.assertEqual(get_token_offsets(token), (0, end_offset, position),
                         'get_token_offsets() should return 0 for start_offset if not found in token')

        # 'end_offset' not present
        token = {'start_offset': start_offset, 'position': position}
        self.assertEqual(get_token_offsets(token), (start_offset, 0, position),
                         'get_token_offsets() should return 0 for end_offset if not found in token')

        # 'position' not present
        token = {'start_offset': start_offset, 'end_offset': end_offset}
        self.assertEqual(get_token_offsets(token), (start_offset, end_offset, 0),
                         'get_token_offsets() should return 0 for position if not found in token')


class HighlightForCustomSentimentTestCase(TestCase):
    """
    highlight_for_custom_sentiment(text, custom_sentiment_id) should
    surround relevant term in text with styled <span>
    """

    def setUp(self):
        self.custom_sentiment_name = 'Hipster'
        self.custom_sentiment = CustomSentimentFactory(name=self.custom_sentiment_name)
        self.locavore = TermFactory(text='locavore', analyzed_text='locavore', custom_sentiment=self.custom_sentiment)
        self.pabst = TermFactory(text='pabst', analyzed_text='pabst', custom_sentiment=self.custom_sentiment)
        self.vinyl = TermFactory(text='vinyl', analyzed_text='vinyl', custom_sentiment=self.custom_sentiment)
        self.text = 'Hashtag direct trade before they sold out aesthetic typewriter locavore prism vinyl.'

        # Get actual return value from sort_terms_by_number_of_words() to set return_value of mock
        self.terms_sorted_by_number_of_words = sort_terms_by_number_of_words([self.locavore, self.vinyl])
        # Get actual return value from get_sentiment_termvector_for_text() to set return_value of mock
        self.termvector = get_sentiment_termvector_for_text(self.text)

    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment', autospec=True)
    def test_highlight_for_custom_sentiment_no_terms(self, mock_get_custom_sentiment):
        """
        Test highlight_for_custom_sentiment() for situations where there are no terms found
        """

        # If no CustomSentiment found with custom_sentiment_id (get_custom_sentiment() returns None),
        # highlight_for_custom_sentiment() should return text
        mock_get_custom_sentiment.return_value = None

        self.assertEqual(highlight_for_custom_sentiment(self.text, custom_sentiment_id=1), self.text,
                'highlight_for_custom_sentiment() should return text if no CustomSentiment found with custom_sentiment_id')

        # If CustomSentiment has no terms, highlight_for_custom_sentiment() should return text
        custom_sentiment = CustomSentimentFactory(name=self.custom_sentiment_name)
        mock_get_custom_sentiment.return_value = custom_sentiment

        self.assertEqual(highlight_for_custom_sentiment(self.text, custom_sentiment_id=custom_sentiment.id),
                         self.text, 'highlight_for_custom_sentiment() should return text if CustomSentiment has no terms')

    @patch('letter_sentiment.custom_sentiment.get_custom_sentiment', autospec=True)
    @patch('letter_sentiment.custom_sentiment.sort_terms_by_number_of_words', autospec=True)
    @patch('letter_sentiment.custom_sentiment.get_sentiment_termvector_for_text', autospec=True)
    @patch('letter_sentiment.custom_sentiment.get_token_offsets', autospec=True)
    @patch('letter_sentiment.custom_sentiment.update_tokens_in_termvector', autospec=True)
    def test_highlight_for_custom_sentiment_terms(self, mock_update_tokens_in_termvector,
                                            mock_get_token_offsets,
                                            mock_get_sentiment_termvector_for_text,
                                            mock_sort_terms_by_number_of_words,
                                            mock_get_custom_sentiment):
        """
        Test highlight_for_custom_sentiment() for situations where there are terms found
        """

        mock_get_custom_sentiment.return_value = self.custom_sentiment
        mock_sort_terms_by_number_of_words.return_value = self.terms_sorted_by_number_of_words
        mock_get_sentiment_termvector_for_text.return_value = self.termvector
        mock_get_token_offsets.return_value = (1, 2, 3)
        mock_update_tokens_in_termvector.return_value = self.termvector

        # sort_terms_by_number_of_words(custom_sentiment.get_terms()) should be called
        highlight_for_custom_sentiment(self.text, custom_sentiment_id=self.custom_sentiment.id)

        args, kwargs = mock_sort_terms_by_number_of_words.call_args
        self.assertEqual(set(args[0]), set([self.locavore, self.pabst, self.vinyl]),
                         'highlight_for_custom_sentiment() should call sort_terms_by_number_of_words()')

        # get_sentiment_termvector_for_text(text) should be called
        args, kwargs = mock_get_sentiment_termvector_for_text.call_args
        self.assertEqual(args[0], self.text,
                         'highlight_for_custom_sentiment() should call get_sentiment_termvector_for_text()')

        # get_token_offsets() should be called twice (once for each term(
        self.assertEqual(mock_get_token_offsets.call_count, 2,
                         'highlight_for_custom_sentiment() should call get_token_offsets() once for each Term in text')


class SortTermsByNumberOfWordsTestCase(TestCase):
    """
    sort_terms_by_number_of_words() should take a list of terms
    and return that list sorted by the number of words, in descending order
    """

    def test_sort_terms_by_number_of_words(self):
        custom_sentiment = CustomSentimentFactory(name='Hipster')
        one_word_term = TermFactory(text='waistcoat', analyzed_text='waistcoat',
                                    custom_sentiment=custom_sentiment)
        two_word_term = TermFactory(text='disrupt gastropub', analyzed_text='disrupt gastropub',
                                    custom_sentiment=custom_sentiment)
        three_word_term = TermFactory(text='sustainable 8-bit kombucha', analyzed_text='sustainable 8-bit kombucha',
                                      custom_sentiment=custom_sentiment)

        unsorted_terms = [two_word_term, one_word_term, three_word_term]
        sorted_terms = [three_word_term, two_word_term, one_word_term]

        self.assertListEqual(sort_terms_by_number_of_words(unsorted_terms), sorted_terms,
                             'sort_terms_by_number_of_words() should sort list of terms by # of words, descending')


class UpdateTokensInTermvectorTestCase(TestCase):
    """
    update_tokens_in_termvector() should do something-or-other with termvector

    If something it's looking for is inside the token, it should remove a search term from the termvector
    to make sure it doesn't get highlighted more than once

    Does this have something to do with n-grams?
    """

    def test_update_tokens_in_termvector(self):
        original_termvector = {
            'box': {'tokens': [{'start_offset': 7, 'end_offset': 10, 'position': 1}], 'term_freq': 1},
            'pounce': {'tokens': [{'start_offset': 0, 'end_offset': 6, 'position': 0}], 'term_freq': 1},
            'pounce box': {'tokens': [{'start_offset': 0, 'end_offset': 10, 'position': 0}], 'term_freq': 1}
        }

        # If an n-gram of the term is inside the token, the termvector should get updated
        term = TermFactory(text='pounce box', analyzed_text='pounce box')
        token = original_termvector['pounce box']['tokens'][0]
        termvector = copy.deepcopy(original_termvector)

        updated_termvector = update_tokens_in_termvector(termvector, term, token)
        self.assertNotEqual(original_termvector, updated_termvector,
                            "If an n-gram of the term is inside the token, the termvector should get updated")

        # If an n-gram of the term is not inside the token, the termvector shouldn't get updated
        term = TermFactory(text='pounce', analyzed_text='pounce')
        token = original_termvector['box']['tokens'][0]
        termvector = copy.deepcopy(original_termvector)

        updated_termvector = update_tokens_in_termvector(termvector, term, token)
        self.assertEqual(original_termvector, updated_termvector,
                         "If an n-gram of the term is not inside the token, the termvector shouldn't get updated")
