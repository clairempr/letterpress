import calendar

from unittest.mock import patch

from django.contrib.admin import site
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from letters.admin import CorrespondentAdmin, DocumentAdmin, DocumentImageAdmin, DocumentSourceAdmin, LetterAdmin
from letters.admin_filters import (
    CorrespondentSourceFilter, get_correspondents_of_source, get_objects_with_date,
    ImageSourceFilter, MonthFilter, RecipientFilter, WriterFilter, YearFilter
)
from letters.models import Correspondent, DocumentImage, DocumentSource, Letter
from letters.tests.factories import (
    CorrespondentFactory, DocumentImageFactory, DocumentSourceFactory,
    EnvelopeFactory, LetterFactory, MiscDocumentFactory
)


class CorrespondentSourceFilterTestCase(TestCase):
    """
    Test CorrespondentSourceFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = CorrespondentAdmin(Correspondent, site)

    @patch('letters.admin_filters.get_source_lookups', autospec=True)
    def test_lookups(self, mock_get_source_lookups):
        """
        lookups() should return get_source_lookups()
        """

        CorrespondentSourceFilter(self.request, params={}, model=DocumentSource, model_admin=self.modeladmin)
        self.assertEqual(mock_get_source_lookups.call_count, 1,
                         'CorrespondentSourceFilter.lookups() should call get_source_lookups()')

    @patch('letters.admin_filters.get_correspondents_of_source', autospec=True)
    def test_queryset(self, mock_get_correspondents_of_source):
        """
        queryset() should return all Correspondents associated with a particular DocumentSource
        by finding out which Correspondents were writers or recipients of Letters, Envelopes,
        and MiscDocuments with this DocumentSource
        """

        misc_doc_and_letter_source = DocumentSourceFactory()
        misc_doc_writer = CorrespondentFactory()
        MiscDocumentFactory(writer=misc_doc_writer, source=misc_doc_and_letter_source)

        letter_writer = CorrespondentFactory()
        letter_recipient = CorrespondentFactory()
        LetterFactory(writer=letter_writer, recipient=letter_recipient, source=misc_doc_and_letter_source)

        envelope_source = DocumentSourceFactory()
        envelope_writer = CorrespondentFactory()
        envelope_recipient = CorrespondentFactory()
        EnvelopeFactory(writer=envelope_writer, recipient=envelope_recipient, source=envelope_source)

        parameter = 'source'

        # When no DocumentSource specified, all Correspondents should be returned
        filter = CorrespondentSourceFilter(self.request, params={}, model=DocumentSource, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Correspondent.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 0,
                         "get_correspondents_of_source() shouldn't be called if no DocumentSource specified")
        self.assertSetEqual(
            set(queryset), set(Correspondent.objects.all()),
            'CorrespondentSourceFilter.queryset() should return all Corresponents if no DocumentSource specified'
        )

        # When DocumentSource is misc_doc_and_letter_source, misc_doc_writer, letter_writer,
        # and letter_recipient should be returned
        mock_get_correspondents_of_source.return_value = set([misc_doc_writer.id, letter_writer.id,
                                                              letter_recipient.id])
        filter = CorrespondentSourceFilter(self.request, params={parameter: misc_doc_and_letter_source.id},
                                           model=DocumentSource, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Correspondent.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 1,
                         'get_correspondents_of_source() should be called if DocumentSource specified')
        mock_get_correspondents_of_source.reset_mock()
        self.assertSetEqual(set(queryset), set([misc_doc_writer, letter_writer, letter_recipient]),
                            'CorrespondentSourceFilter.queryset() should return Corresponents for DocumentSource')

        # When DocumentSource is envelope_source, envelope_writer and envelope_recipient should be returned
        mock_get_correspondents_of_source.return_value = set([envelope_writer.id, envelope_recipient.id])
        filter = CorrespondentSourceFilter(self.request, params={parameter: envelope_source.id}, model=DocumentSource,
                                           model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Correspondent.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 1,
                         'get_correspondents_of_source() should be called if DocumentSource specified')
        mock_get_correspondents_of_source.reset_mock()
        self.assertSetEqual(set(queryset), set([envelope_writer, envelope_recipient]),
                            'CorrespondentSourceFilter.queryset() should return Corresponents for DocumentSource')


class GetCorrespondentsOfSourceTestCase(TestCase):
    """
    get_correspondents_of_source() should get a unique list of Correspondent ids
    associated with a DocumentSource id through letters, envelopes, and misc. documents
    """

    def test_get_correspondents_of_source(self):
        misc_doc_and_letter_source = DocumentSourceFactory()
        misc_doc_writer = CorrespondentFactory()
        MiscDocumentFactory(writer=misc_doc_writer, source=misc_doc_and_letter_source)

        letter_writer = CorrespondentFactory()
        letter_recipient = CorrespondentFactory()
        LetterFactory(writer=letter_writer, recipient=letter_recipient, source=misc_doc_and_letter_source)

        envelope_source = DocumentSourceFactory()
        envelope_writer = CorrespondentFactory()
        envelope_recipient = CorrespondentFactory()
        EnvelopeFactory(writer=envelope_writer, recipient=envelope_recipient, source=envelope_source)

        # Correspondent not associated with either DocumentSource
        CorrespondentFactory()

        # When DocumentSource is misc_doc_and_letter_source, ids for misc_doc_writer, letter_writer,
        # and letter_recipient should be returned
        self.assertSetEqual(
            set(get_correspondents_of_source(misc_doc_and_letter_source.id)),
            set([misc_doc_writer.id, letter_writer.id, letter_recipient.id]),
            'get_correspondents_of_source() should return unique set of ids of Corresponents for DocumentSource'
        )

        # When DocumentSource is envelope_source, ids for envelope_writer and envelope_recipient
        # should be returned
        self.assertSetEqual(
            set(get_correspondents_of_source(envelope_source.id)),
            set([envelope_writer.id, envelope_recipient.id]),
            'get_correspondents_of_source() should return unique set of ids of Corresponents for DocumentSource'
        )


class GetObjectsWithDateTestCase(TestCase):
    """
    get_objects_with_date() should return model objects where date isn't empty
    """

    def test_get_objects_with_date(self):
        dated_letter = LetterFactory(date='1890-04-01')
        LetterFactory()

        self.assertSetEqual(set(get_objects_with_date(Letter)), set([dated_letter]))


class GetSourceLookupsTestCase(TestCase):
    """
    get_source_lookups() should return a list of tuples with id and name of DocumentSources
    """

    def test_get_source_lookups(self):
        source1 = DocumentSourceFactory(name='DocumentSource 1')
        source2 = DocumentSourceFactory(name='DocumentSource 2')

        modeladmin = DocumentSourceAdmin(DocumentSource, site)
        request = RequestFactory().get('/')
        filter = CorrespondentSourceFilter(request, params='', model=DocumentSource, model_admin=modeladmin)
        expected = [(source1.id, source1.name), (source2.id, source2.name)]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))


class ImageSourceFilterTestCase(TestCase):
    """
    Test ImageSourceFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = DocumentImageAdmin(DocumentImage, site)

    @patch('letters.admin_filters.get_source_lookups', autospec=True)
    def test_lookups(self, mock_get_source_lookups):
        """
        lookups() should return get_source_lookups()
        """

        ImageSourceFilter(self.request, params={}, model=DocumentImage, model_admin=self.modeladmin)
        self.assertEqual(mock_get_source_lookups.call_count, 1,
                         'ImageSourceFilter.lookups() should call get_source_lookups()')

    @patch('letters.admin_filters.get_correspondents_of_source', autospec=True)
    def test_queryset(self, mock_get_correspondents_of_source):
        """
        queryset() should return all DocumentImages associated with a particular DocumentSource
        by finding out which DocumentImages were images of Letters, Envelopes, and MiscDocuments
        with this DocumentSource
        """

        letter_source = DocumentSourceFactory()
        letter_writer = CorrespondentFactory()
        letter_recipient = CorrespondentFactory()
        letter = LetterFactory(writer=letter_writer, recipient=letter_recipient, source=letter_source)
        letter_image = DocumentImageFactory()
        letter.images.add(letter_image)

        envelope_source = DocumentSourceFactory()
        envelope_writer = CorrespondentFactory()
        envelope_recipient = CorrespondentFactory()
        envelope = EnvelopeFactory(writer=envelope_writer, recipient=envelope_recipient, source=envelope_source)
        envelope_image = DocumentImageFactory()
        envelope.images.add(envelope_image)

        correspondent_with_image_source = DocumentSourceFactory()
        correspondent_with_image = CorrespondentFactory()
        LetterFactory(writer=correspondent_with_image, source=correspondent_with_image_source)
        correspondent_image = DocumentImageFactory()
        correspondent_with_image.images.add(correspondent_image)

        parameter = 'source'

        # When no DocumentSource specified, all DocumentImages should be returned
        filter = ImageSourceFilter(self.request, params={}, model=DocumentImage, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, DocumentImage.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 0,
                         "get_correspondents_of_source() shouldn't be called if no DocumentSource specified")
        self.assertSetEqual(
            set(queryset), set(DocumentImage.objects.all()),
            'ImageSourceFilter.queryset() should return all DocumentImages if no DocumentSource specified'
        )

        # When DocumentSource is letter_source, letter_image should be returned
        mock_get_correspondents_of_source.return_value = set([letter_writer.id, letter_recipient.id])
        filter = ImageSourceFilter(self.request, params={parameter: letter_source.id}, model=DocumentImage,
                                   model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, DocumentImage.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 1,
                         'get_correspondents_of_source() should be called if DocumentSource specified')
        mock_get_correspondents_of_source.reset_mock()
        self.assertSetEqual(set(queryset), set([letter_image]),
                            'ImageSourceFilter.queryset() should return DocumentImages for DocumentSource')

        # When DocumentSource is envelope_source, envelope_image should be returned
        mock_get_correspondents_of_source.return_value = set([envelope_writer.id, envelope_recipient.id])
        filter = ImageSourceFilter(self.request, params={parameter: envelope_source.id}, model=DocumentImage,
                                   model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, DocumentImage.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 1,
                         'get_correspondents_of_source() should be called if DocumentSource specified')
        mock_get_correspondents_of_source.reset_mock()
        self.assertSetEqual(set(queryset), set([envelope_image]),
                            'ImageSourceFilter.queryset() should return DocumentImages for DocumentSource')

        # When DocumentSource is correspondent_with_image_source, correspondent_image should be returned
        mock_get_correspondents_of_source.return_value = set([correspondent_with_image.id])
        filter = ImageSourceFilter(self.request, params={parameter: correspondent_with_image.id}, model=DocumentImage,
                                   model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, DocumentImage.objects.all())
        self.assertEqual(mock_get_correspondents_of_source.call_count, 1,
                         'get_correspondents_of_source() should be called if DocumentSource specified')
        mock_get_correspondents_of_source.reset_mock()
        self.assertSetEqual(set(queryset), set([correspondent_image]),
                            'ImageSourceFilter.queryset() should return DocumentImages for DocumentSource')


class MonthFilterTestCase(TestCase):
    """
    Test MonthFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = DocumentAdmin(Letter, site)

        self.sept_1862_letter = LetterFactory(date='1862-09-00')
        self.may_1863_letter = LetterFactory(date='1863-05-00')

    @patch('letters.admin_filters.get_objects_with_date', autospec=True)
    def test_lookups(self, mock_get_objects_with_date):
        """
        lookups() should return all the months for which a dated Document exists
        """

        mock_get_objects_with_date.return_value = Letter.objects.filter(pk__in=[self.sept_1862_letter.id,
                                                                                self.may_1863_letter.id])
        filter = MonthFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        self.assertEqual(mock_get_objects_with_date.call_count, 1,
                         'MonthFilter.lookups() should call get_objects_with_date()')
        expected = [(5, calendar.month_name[5]), (9, calendar.month_name[9])]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    # Patch MonthFilter and YearFilter lookups because get_objects_with_date will get called once for each
    @patch.object(MonthFilter, 'lookups', autospec=True)
    @patch.object(YearFilter, 'lookups', autospec=True)
    @patch('letters.admin_filters.get_objects_with_date', autospec=True)
    def test_queryset(self, mock_get_objects_with_date, mock_YearFilter_lookups, mock_MonthFilter_lookups):
        """
        queryset() should return all the objects that have a date in the given month, if specified
        Otherwise it should return all the objects
        """

        mock_get_objects_with_date.return_value = Letter.objects.all()

        parameter = 'month'

        # When no month specified, all Letters should be returned
        filter = MonthFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertEqual(mock_get_objects_with_date.call_count, 0,
                         "get_objects_with_date() shouldn't be called if no month specified")
        self.assertSetEqual(set(queryset), set(Letter.objects.all()),
                            'MonthFilter.queryset() should return all objects if no month specified')

        # When month specified, only Letters with a date in that month should be returned
        filter = MonthFilter(self.request, params={parameter: '5'}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertEqual(mock_get_objects_with_date.call_count, 1,
                         'get_objects_with_date() should be called if month specified')
        mock_get_objects_with_date.reset_mock()
        self.assertSetEqual(set(queryset), set([self.may_1863_letter]),
                            'MonthFilter.queryset() should return letters with dates in specified month')


class RecipientFilterTestCase(TestCase):
    """
    Test RecipientFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = LetterAdmin(Letter, site)

        self.letter_recipient1 = CorrespondentFactory()
        self.letter1 = LetterFactory(recipient=self.letter_recipient1)

        self.letter_recipient2 = CorrespondentFactory()
        self.letter2 = LetterFactory(recipient=self.letter_recipient2)

        EnvelopeFactory(recipient=CorrespondentFactory())

    def test_lookups(self):
        """
        lookups() should be a list of (recipient.id, recipient.to_string()) for
        known recipients of the admin document type
        """

        filter = RecipientFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        expected = [(self.letter_recipient1.id, self.letter_recipient1.to_string()),
                    (self.letter_recipient2.id, self.letter_recipient2.to_string())]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    def test_queryset(self):
        """
        queryset() should return all the Letters with the given recipient, if specified
        Otherwise it should return all the Letters
        """

        parameter = 'recipient'

        # When no recipient specified, all Letters should be returned
        filter = RecipientFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set(Letter.objects.all()),
                            'RecipientFilter.queryset() should return all objects if no recipient specified')

        # When recipient specified, only Letters with that recipient should be returned
        filter = RecipientFilter(self.request, params={parameter: self.letter_recipient1.id}, model=Letter,
                                 model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set([self.letter1]),
                            'RecipientFilter.queryset() should return letters with the specified recipient')


class WriterFilterTestCase(TestCase):
    """
    Test WriterFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = LetterAdmin(Letter, site)

        self.letter_writer1 = CorrespondentFactory()
        self.letter1 = LetterFactory(writer=self.letter_writer1)

        self.letter_writer2 = CorrespondentFactory()
        self.letter2 = LetterFactory(writer=self.letter_writer2)

        EnvelopeFactory(writer=CorrespondentFactory())

    def test_lookups(self):
        """
        lookups() should be a list of (writer.id, writer.to_string()) for
        known writers of the admin document type
        """

        filter = WriterFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        expected = [(self.letter_writer1.id, self.letter_writer1.to_string()),
                    (self.letter_writer2.id, self.letter_writer2.to_string())]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    def test_queryset(self):
        """
        queryset() should return all the Letters with the given writer, if specified
        Otherwise it should return all the Letters
        """

        parameter = 'writer'

        # When no writer specified, all Letters should be returned
        filter = WriterFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set(Letter.objects.all()),
                            'WriterFilter.queryset() should return all objects if no writer specified')

        # When writer specified, only Letters with that writer should be returned
        filter = WriterFilter(self.request, params={parameter: self.letter_writer1.id}, model=Letter,
                              model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set([self.letter1]),
                            'WriterFilter.queryset() should return letters with the specified writer')


class YearFilterTestCase(TestCase):
    """
    Test YearFilter
    """

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.modeladmin = DocumentAdmin(Letter, site)

        self.sept_1862_letter = LetterFactory(date='1862-09-00')
        self.may_1863_letter = LetterFactory(date='1863-05-00')

    @patch('letters.admin_filters.get_objects_with_date', autospec=True)
    def test_lookups(self, mock_get_objects_with_date):
        """
        lookups() should return all the years for which a dated Document exists
        """

        mock_get_objects_with_date.return_value = Letter.objects.filter(pk__in=[self.sept_1862_letter.id,
                                                                                self.may_1863_letter.id])
        filter = YearFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        self.assertEqual(mock_get_objects_with_date.call_count, 1,
                         'YearFilter.lookups() should call get_objects_with_date()')
        expected = [(1862, 1862), (1863, 1863)]
        self.assertEqual(sorted(filter.lookup_choices), sorted(expected))

    # Patch MonthFilter and YearFilter lookups because get_objects_with_date will get called once for each
    @patch.object(MonthFilter, 'lookups', autospec=True)
    @patch.object(YearFilter, 'lookups', autospec=True)
    def test_queryset(self, mock_YearFilter_lookups, mock_MonthFilter_lookups):
        """
        queryset() should return all the objects that have a date in the given year, if specified
        Otherwise it should return all the objects
        """

        parameter = 'year'

        # When no year specified, all Letters should be returned
        filter = YearFilter(self.request, params={}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set(Letter.objects.all()),
                            'YearFilter.queryset() should return all objects if no year specified')

        # When month specified, only Letters with a date in that year should be returned
        filter = YearFilter(self.request, params={parameter: '1862'}, model=Letter, model_admin=self.modeladmin)
        queryset = filter.queryset(self.request, Letter.objects.all())
        self.assertSetEqual(set(queryset), set([self.sept_1862_letter]),
                            'MonthFilter.queryset() should return letters with dates in specified year')
