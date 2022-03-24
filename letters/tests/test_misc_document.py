from django.test import TestCase

from unittest.mock import patch

from letters.tests.factories import MiscDocumentFactory


class MiscDocumentTestCase(TestCase):
    """
    Test MiscDocument model
    """

    def test_get_display_string(self):
        """
        MiscDocument.get_display_string() should return MiscDocument.description
        """

        misc_document = MiscDocumentFactory(description='Underpants gnome business plan')
        self.assertEqual(misc_document.get_display_string(), misc_document.description,
                         'MiscDocument.get_display_string() should return MiscDocument.description')

    @patch('letters.models.misc_document.get_envelope_preview', autospec=True)
    def test_envelope_preview(self, mock_get_envelope_preview):
        """
        MiscDocument.envelope_preview() should return get_envelope_preview(misc_document)
        """

        mock_get_envelope_preview.return_value = 'envelope preview'

        misc_document = MiscDocumentFactory()
        envelope_preview = misc_document.envelope_preview()

        args, kwargs = mock_get_envelope_preview.call_args
        self.assertEqual(args[0], misc_document,
                         'MiscDocument.envelope_preview() should call get_envelope_preview(misc_document)')
        self.assertEqual(envelope_preview, mock_get_envelope_preview.return_value,
                         'MiscDocument.envelope_preview() should return value of get_envelope_preview(misc_document)')
