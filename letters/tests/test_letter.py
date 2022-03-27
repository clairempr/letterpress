from django_date_extensions.fields import ApproximateDate

from unittest.mock import patch

from django.test import TestCase

from letters.es_settings import ES_CLIENT
from letters.models import Letter
from letters.tests.factories import CorrespondentFactory, DocumentSourceFactory, LetterFactory, PlaceFactory


class LetterTestCase(TestCase):
    """
    Test Letter model
    """

    @patch.object(Letter, 'list_date', autospec=True)
    def test_get_display_string(self, mock_list_date):
        """
        Letter.get_display_string() should return formatted string containing lost_date, writer, and recipient
        """

        mock_list_date.return_value = 'list date'

        writer = CorrespondentFactory()
        recipient = CorrespondentFactory()
        letter = LetterFactory(writer=writer, recipient=recipient)

        display_string = letter.get_display_string()
        self.assertIn(str(writer), display_string,
                      'Letter.get_display_string() should return string containing writer')
        self.assertIn(str(recipient), display_string,
                      'Letter.get_display_string() should return string containing recipient')
        self.assertIn(mock_list_date.return_value, display_string,
                      'Letter.get_display_string() should return string containing list_date')

    def test__lt__(self):
        """
        Letter.__lt__() should return True if self.to_string()
        comes before other letter.to_string() in alphabetic sorting,
        otherwise it should return False
        """

        # Letters should be ordered by display string: list_date, writer, recipient
        writer = CorrespondentFactory()
        recipient = CorrespondentFactory()
        letter_from_1862 = LetterFactory(date=ApproximateDate(1862), writer=writer, recipient=recipient)
        letter_from_1861 = LetterFactory(date=ApproximateDate(1861), writer=writer, recipient=recipient)
        other_letter_from_1861 = LetterFactory(date=ApproximateDate(1861), writer=writer, recipient=recipient)

        self.assertTrue(letter_from_1861 < letter_from_1862,
                        '{} should be < {}'.format(letter_from_1861, letter_from_1862))
        self.assertFalse(letter_from_1861 < other_letter_from_1861,
                         "{} shouldn't be be < {}".format(letter_from_1861, other_letter_from_1861))
        self.assertFalse(letter_from_1862 < letter_from_1861,
                         "{} shouldn't be be < {}".format(letter_from_1862, letter_from_1861))

    @patch('letters.models.letter.get_envelope_preview', autospec=True)
    def test_envelope_preview(self, mock_get_envelope_preview):
        """
        Letter.envelope_preview() should return get_envelope_preview()
        """

        mock_get_envelope_preview.return_value = 'envelope preview'

        letter = LetterFactory()
        envelope_preview = letter.envelope_preview()

        args, kwargs = mock_get_envelope_preview.call_args
        self.assertEqual(args[0], letter, 'Letter.envelope_preview() should call get_envelope_preview(letter)')
        self.assertEqual(envelope_preview, mock_get_envelope_preview.return_value,
                         'Letter.envelope_preview() should return value of get_envelope_preview(letter)')

    @patch('letters.models.letter.html_to_text', autospec=True)
    def test_body_as_text(self, mock_html_to_text):
        """
        Letter.body_as_text() should return html_to_text()
        """

        mock_html_to_text.return_value = 'html to text'

        letter = LetterFactory(body='Wish you were here')
        body_as_text = letter.body_as_text()

        args, kwargs = mock_html_to_text.call_args
        self.assertEqual(args[0], letter.body, 'Letter.body_as_text() should call html_to_text(letter.body)')
        self.assertEqual(body_as_text, mock_html_to_text.return_value,
                         'Letter.body_as_text() should return value of html_to_text(letter)')

    @patch.object(Letter, 'body_as_text', autospec=True)
    def test_contents(self, mock_body_as_text):
        """
        Letter.contents() should contain letter heading, greeting, body_as_text(),
        closing, signature, and ps
        """

        mock_body_as_text.return_value = 'As this is the beginin of a new year I thought as I was a lone to night I ' \
                                         'would write you a few lines to let you know that we are not all ded yet.'

        letter = Letter(heading='Januery the 1st / 62',
                        greeting='Miss Evey',
                        closing='your friend as every',
                        signature='F.P. Black',
                        ps='p.s. remember me to enquirin friends')

        contents = letter.contents()

        self.assertIn(letter.heading, contents, 'Letter.contents() should include Letter.heading')
        self.assertIn(letter.greeting, contents, 'Letter.contents() should include Letter.greeting')
        self.assertIn(mock_body_as_text.return_value, contents,
                      'Letter.contents() should include Letter.body_as_text()')
        self.assertIn(letter.closing, contents, 'Letter.contents() should include Letter.closing')
        self.assertIn(letter.signature, contents, 'Letter.contents() should include Letter.signature')
        self.assertIn(letter.ps, contents, 'Letter.contents() should include Letter.ps')

        # If letter is completely blank, Letter.contents() should return empty string
        mock_body_as_text.return_value = ''
        self.assertEqual(LetterFactory().contents(), '',
                         'If letter is completely blank, Letter.contents() should return empty string')

    @patch.object(Letter, 'contents', autospec=True)
    @patch('letters.models.letter.get_sentiment', autospec=True)
    def test_sentiment(self, mock_get_sentiment, mock_contents):
        """
        Letter.sentiment() should return get_sentiment(letter.contents())
        """

        mock_contents.return_value = 'contents'
        mock_get_sentiment.return_value = 'sentiment'

        letter = LetterFactory()

        sentiment = letter.sentiment()
        args, kwargs = mock_get_sentiment.call_args
        self.assertEqual(args[0], mock_contents.return_value,
                         'Letter.sentiment() should call get_sentiment(letter.contents())')
        self.assertEqual(sentiment, mock_get_sentiment.return_value,
                         'Letter.sentiment() should return value of get_sentiment(letter.contents())')

    @patch.object(Letter, 'field_es_repr', autospec=True)
    def test_es_repr(self, mock_field_es_repr):
        """
        Letter.es_repr() should return a dict with fields in es_mapping mapped to field_es_repr()
        for each field
        """

        letter = LetterFactory()

        data = letter.es_repr()
        self.assertEqual(data['_id'], letter.pk, "Letter.es_repr() should return a dict with '_id' = letter.pk")
        self.assertGreater(mock_field_es_repr.call_count, 0,
                           'Letter.es_repr() should call Letter.field_es_repr() at least once')

    @patch.object(Letter, 'get_es_contents', autospec=True)
    @patch.object(Letter, 'get_es_date', autospec=True)
    @patch.object(Letter, 'get_es_writer', autospec=True)
    @patch.object(Letter, 'get_es_source', autospec=True)
    def test_field_es_repr(self, mock_get_es_source, mock_get_es_writer, mock_get_es_date, mock_get_es_contents):
        """
        Letter.field_es_repr() should return serialize letter fields for Elasticsearch indexing
        by doing the following:
        Get field description from mapping
        If there's a method named get_es_{field name} – use it to get field's value
        If it's an object, populate a dictionary directly from attributes of the related object
        If it's not an object, and there's no special method with special name, get an attribute from the model

        See https://qbox.io/blog/elasticsearch-and-django-bulk-index/
        """

        place = PlaceFactory(name='Manassas Junction')
        letter = LetterFactory(heading='Januery the 1st / 62', place=place)

        # If there's a method named get_es_{field name}, it should be used to get field's value
        letter.field_es_repr('contents')
        self.assertEqual(mock_get_es_contents.call_count, 1,
                         'Letter.field_es_repr() should call get_es_contents() for contents()')

        letter.field_es_repr('date')
        self.assertEqual(mock_get_es_contents.call_count, 1,
                         'Letter.field_es_repr() should call get_es_date() for date field')

        letter.field_es_repr('writer')
        self.assertEqual(mock_get_es_writer.call_count, 1,
                         'Letter.field_es_repr() should call get_es_writer() for writer field')

        letter.field_es_repr('source')
        self.assertEqual(mock_get_es_source.call_count, 1,
                         'Letter.field_es_repr() should call get_es_source() for source field')

        # If it's an object, a dictionary should be populated directly from attributes of the related object

        # There aren't currently any fields like this in the mapping, so add one here to test it
        Letter._meta.es_mapping['properties']['place'] = {'type': 'object',
                                                          'properties': {'name': 'name'}}
        result = letter.field_es_repr('place')
        self.assertEqual(result['_id'], place.id,
                    "If field is an object, Letter.field_es_repr() should return a dictionary with object's attributes")
        self.assertEqual(result['name'], place.name,
                    "If field is an object, Letter.field_es_repr() should return a dictionary with object's attributes")

        # If it's not an object, and there's no special method with special name,
        # field_es_repr() should get an attribute from the model

        # There aren't currently any fields like this in the mapping, so add one here to test it
        Letter._meta.es_mapping['properties']['heading'] = {'type': 'something else'}
        result = letter.field_es_repr('heading')
        self.assertEqual(result, letter.heading,
                         "Letter.field_es_repr() should return the field's value if it doesn't have its own method")

    @patch.object(Letter, 'contents', autospec=True)
    def test_get_es_contents(self, mock_contents):
        """
        Letter.get_es_contents() should return Letter.contents()
        """

        mock_contents.return_value = 'Contents'

        self.assertEqual(LetterFactory().get_es_contents(), mock_contents.return_value,
                         'Letter.get_es_contents() should return Letter.contents()')

    @patch.object(Letter, 'index_date', autospec=True)
    def test_get_es_date(self, mock_index_date):
        """
        Letter.get_es_date() should return Letter.index_date()
        """

        mock_index_date.return_value = 'index date'

        self.assertEqual(LetterFactory().get_es_date(), mock_index_date.return_value,
                         'Letter.get_es_date() should return Letter.index_date()')

    def test_get_es_writer(self):
        """
        Letter.get_es_writer() should return Letter.writer.id
        """

        letter = LetterFactory()
        self.assertEqual(letter.get_es_writer(), letter.writer.id,
                         'Letter.get_es_writer() should return Letter.writer.id')

    def test_get_es_source(self):
        """
        Letter.get_es_source() should return Letter.source.id
        """

        letter = LetterFactory()
        self.assertEqual(letter.get_es_source(), letter.source.id,
                         'Letter.get_es_source() should return Letter.source.id')

    @patch.object(Letter, 'create_or_update_in_elasticsearch', autospec=True)
    def test_save(self, mock_create_or_update_in_elasticsearch):
        """
        Letter.save() should call Letter.create_or_update_in_elasticsearch()
        """

        letter = Letter(writer=CorrespondentFactory(), recipient=CorrespondentFactory(), source=DocumentSourceFactory(),
                        place=PlaceFactory())
        letter.save()
        args, kwargs = mock_create_or_update_in_elasticsearch.call_args
        self.assertIsNone(kwargs['is_new'],
                          'Letter.save() should call create_or_update_in_elasticsearch(None) on Letter creation')

        letter.save()
        args, kwargs = mock_create_or_update_in_elasticsearch.call_args
        self.assertIsNotNone(kwargs['is_new'],
                             'Letter.save() should call create_or_update_in_elasticsearch(None) on Letter update')

    @patch.object(Letter, 'es_repr', autospec=True)
    @patch.object(ES_CLIENT, 'create', autospec=True)
    @patch.object(ES_CLIENT, 'update', autospec=True)
    def test_create_or_update_in_elasticsearch(self, mock_update, mock_create, mock_es_repr):
        """
        If this is a newly-created Letter that hasn't been assigned a pk yet,
        it should get indexed in Elasticsearch

        If it's an existing Letter, Elasticsearch index should get updated
        """

        letter = LetterFactory()
        letter.create_or_update_in_elasticsearch(is_new=None)

        self.assertEqual(mock_es_repr.call_count, 1,
                         'Letter.create_or_update_in_elasticsearch() should call Letter.es_repr()')

        # When create_or_update_in_elasticsearch() called with is_new = None, ES_CLIENT.create() should get called
        self.assertEqual(mock_create.call_count, 1,
            'When create_or_update_in_elasticsearch(is_new=None) called, ES_CLIENT.create() should get called')

        # When create_or_update_in_elasticsearch() called with is_new not None, ES_CLIENT.update() should get called
        letter.create_or_update_in_elasticsearch(is_new=letter.pk)
        self.assertEqual(mock_update.call_count, 1,
            'When create_or_update_in_elasticsearch(is_new=not None) called, ES_CLIENT.mock_update() should get called')

    @patch.object(Letter, 'delete_from_elasticsearch', autospec=True)
    def test_delete(self, mock_delete_from_elasticsearch):
        """
        Letter.delete() should call delete_from_elasticsearch(letter.pk)
        """

        letter = Letter(pk=1, writer=CorrespondentFactory(), recipient=CorrespondentFactory())
        letter_pk = letter.pk
        letter.delete()

        args, kwargs = mock_delete_from_elasticsearch.call_args
        self.assertEqual(args[1], letter_pk, 'Letter.delete() should call delete_from_elasticsearch(letter.pk)')

    @patch.object(ES_CLIENT, 'delete', autospec=True)
    def test_delete_from_elasticsearch(self, mock_delete):
        """
        Letter.delete_from_elasticsearch() should call ES_CLIENT.delete()
        """

        letter = LetterFactory()
        letter.delete_from_elasticsearch(letter.pk)

        args, kwargs = mock_delete.call_args
        self.assertEqual(kwargs['id'], letter.pk,
                         'Letter.delete_from_elasticsearch() should call ES_CLIENT.delete()')
