from unittest.mock import patch

from django.test import TestCase

from letters.models import Correspondent
from letters.tests.factories import CorrespondentFactory


class CorrespondentTestCase(TestCase):
    """
    Test Correspondent model
    """

    @patch.object(Correspondent, 'get_display_string', autospec=True)
    def test__str__(self, mock_get_display_string):
        """
        Correspondent.__str__() should return Correspondent.get_display_string()
        """

        mock_get_display_string.return_value = 'correspondent str'

        correspondent = CorrespondentFactory()
        correspondent_str = str(correspondent)
        self.assertEqual(correspondent_str, mock_get_display_string.return_value,
                         '__str__() should return value of Correspondent.get_display_string()')

    def test__lt__(self):
        """
        Correspondent.__lt__() should return True if self.to_string()
        comes before other correspondent.to_string() in alphabetic sorting,
        otherwise it should return False
        """

        kate_derenberger = CorrespondentFactory(last_name='Derenberger', first_names='Kate')
        francis_black = CorrespondentFactory(last_name='Black', first_names='Francis P.')
        other_francis_black = CorrespondentFactory(last_name='Black', first_names='Francis P.')

        self.assertTrue(francis_black < kate_derenberger, '{} should be < {}'.format(francis_black, kate_derenberger))
        self.assertFalse(francis_black < other_francis_black,
                        "{} shouldn't be be < {}".format(francis_black, other_francis_black))
        self.assertFalse(kate_derenberger < francis_black,
                        "{} shouldn't be be < {}".format(kate_derenberger, francis_black))

    @patch.object(Correspondent, 'get_display_string', autospec=True)
    def test_to_string(self, mock_get_display_string):
        """
        Correspondent.to_string() should return Correspondent.get_display_string()
        """

        mock_get_display_string.return_value = 'correspondent str'

        correspondent = CorrespondentFactory()
        self.assertEqual(correspondent.to_string(), mock_get_display_string.return_value,
                         'to_string() should return value of Correspondent.get_display_string()')

    def test_get_display_string(self):
        """
        Correspondent.get_display_string() should return string that contains the following,
        if they're filled: last_name, first_names, married_name, suffix
        """

        last_name = 'Waite'
        first_names = 'Elizabeth A.'
        married_name = 'Howard'
        suffix = 'Suffix'

        correspondent = CorrespondentFactory(last_name=last_name, first_names='')
        self.assertIn(correspondent.last_name, correspondent.get_display_string(),
                      'Correspondent.get_display_string() should include last_name if filled')

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names)
        self.assertIn(correspondent.first_names, correspondent.get_display_string(),
                      'Correspondent.get_display_string() should include first_names if filled')

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names, married_name=married_name)
        self.assertIn(correspondent.married_name, correspondent.get_display_string(),
                      'Correspondent.get_display_string() should include married_name if filled')

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names, married_name=married_name,
                                             suffix=suffix)
        self.assertIn(correspondent.suffix, correspondent.get_display_string(),
                      'Correspondent.get_display_string() should include suffix if filled')

    def test_to_export_string(self):
        """
        Correspondent.to_export_string() should include last_name, and first_names and suffix, if they're filled
        """

        last_name = 'Waite'
        first_names = 'Elizabeth A.'
        married_name = 'Howard'
        suffix = 'Suffix'

        correspondent = CorrespondentFactory(last_name=last_name, first_names='')
        self.assertIn(correspondent.last_name, correspondent.to_export_string(),
                      'Correspondent.to_export_string() should include last_name if filled')

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names)
        self.assertIn(correspondent.first_names, correspondent.to_export_string(),
                      'Correspondent.to_export_string() should include first_names if filled')

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names, married_name=married_name)
        self.assertNotIn(correspondent.married_name, correspondent.to_export_string(),
                      "Correspondent.to_export_string() shouldn't include married_name if filled")

        correspondent = CorrespondentFactory(last_name=last_name, first_names=first_names, married_name=married_name,
                                             suffix=suffix)
        self.assertIn(correspondent.suffix, correspondent.to_export_string(),
                      'Correspondent.to_export_string() should include suffix if filled')#     def to_export_string(self):

    @patch('letters.models.correspondent.get_image_preview', autospec=True)
    def test_image_preview(self, mock_get_image_preview):
        """
        Correspondent.image_preview() should return Correspondent.get_image_preview()
        """

        mock_get_image_preview.return_value = 'image_preview'

        correspondent = CorrespondentFactory()
        self.assertEqual(correspondent.image_preview(), mock_get_image_preview.return_value,
                         '__str__() should return value of Correspondent.get_image_preview()')


