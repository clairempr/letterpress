from enum import Enum
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from letters.models import DocumentImage, Envelope
from letters.models.util import get_envelope_preview, get_image_preview, html_to_text
from letters.tests.factories import DocumentImageFactory, EnvelopeFactory, LetterFactory


class GetEnvelopePreviewTestCase(TestCase):
    """
    get_envelope_preview(obj) should return &nbsp;-separated list of envelope image previews for document
    """

    @patch.object(Envelope, 'image_preview', autospec=True)
    def test_get_envelope_preview(self, mock_image_preview):
        mock_image_preview.return_value = 'image preview'

        letter = LetterFactory()

        number_of_envelopes = 2
        for _ in range(number_of_envelopes):
            letter.envelopes.add(EnvelopeFactory())

        envelope_preview = get_envelope_preview(letter)

        # get_envelope_preview() should call Envelope.image_preview() <number_of_envelopes> times
        self.assertEqual(mock_image_preview.call_count, number_of_envelopes,
                         'get_envelope_preview() should call Envelope.image_preview() <number_of_envelopes> times')
        self.assertEqual(envelope_preview.count(mock_image_preview.return_value), number_of_envelopes,
                        'get_envelope_preview() should contain image_preview() for each envelope')

        # Envelope preview should contain number_of_envelopes - 1 '&nbsp;'
        # because the list is &nbsp;-separated
        self.assertEqual(envelope_preview.count('&nbsp;'), number_of_envelopes - 1,
                         'get_envelope_preview() should return &nbsp;-separated list of image previews')


class GetImagePreviewTestCase(TestCase):
    """
    get_image_preview() should return &nbsp;-separated list of image tags for document
    """

    @patch.object(DocumentImage, 'image_tag', autospec=True)
    def test_get_image_preview(self, mock_image_tag):
        mock_image_tag.return_value = 'image tag'

        letter = LetterFactory()

        number_of_images = 2
        for _ in range(number_of_images):
            letter.images.add(DocumentImageFactory())

        image_preview = get_image_preview(letter)

        # get_image_preview() should call DocumentImage.image_tag() <number_of_images> times
        self.assertEqual(mock_image_tag.call_count, number_of_images,
                         'get_image_preview() should call DocumentImage.image_tag() <number_of_images> times')
        self.assertEqual(image_preview.count(mock_image_tag.return_value), number_of_images,
                        'get_image_preview() should contain image_tag() for each image')

        # Image preview should contain number_of_images - 1 '&nbsp;'
        # because the list is &nbsp;-separated
        self.assertEqual(image_preview.count('&nbsp;'), number_of_images - 1,
                         'get_image_preview() should return &nbsp;-separated list of image previews')


class HtmlToTextTestCase(SimpleTestCase):
    """
    html_to_text() should convert an html snippet to text using BeautifulSoup
    """

    def test_html_to_text(self):

        html = '<div>Some text<br>Some more text<br>Even more text</div>'
        text = html_to_text(html)

        for str in ['Some text', 'Some more text', 'Even more text']:
            self.assertIn(str, text, 'html_to_text() should return text containing strings from html snippet')
        for element in ['<div>', '</div>', '<br>']:
            self.assertNotIn(element, text, "html_to_text() should return text that doesn't contain html")
        self.assertEqual(text.count('\n'), 2, "html_to_text() should replace '<br>' with '\n'")
