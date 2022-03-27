from django_date_extensions.fields import ApproximateDate
from django.test import TestCase

from letters.tests.factories import CorrespondentFactory, EnvelopeFactory


class EnvelopeTestCase(TestCase):
    """
    Test Envelope model
    """

    def test_get_display_string(self):
        """
        Envelope.get_display_string() should return description if filled
        Otherwise it should return formatted string containing writer, recipient, and date if filled
        """

        # If description filled, get_display_string() should return description
        envelope = EnvelopeFactory(description='Pink envelope that says URGENT! OPEN IMMEDIATELY!')
        self.assertEqual(envelope.get_display_string(), envelope.description,
                         'If Envelope.description filled, get_display_string() should return description')

        # If description not filled, get_display_string() should return string containing
        # writer, recipient, and date if filled
        # writer and recipient are required fields
        writer = CorrespondentFactory()
        recipient = CorrespondentFactory()
        envelope = EnvelopeFactory(writer=writer, recipient=recipient)

        display_string = envelope.get_display_string()
        self.assertIn(str(writer), display_string,
                      'Correspondent.get_display_string() should return string containing writer')
        self.assertIn(str(recipient), display_string,
                      'Correspondent.get_display_string() should return string containing recipient')

        # If date filled, Envelope.get_display_string() should return string containing date
        envelope = EnvelopeFactory(writer=writer, recipient=recipient, date=ApproximateDate(1863, 7, 1))

        display_string = envelope.get_display_string()
        self.assertIn(str(envelope.date), display_string,
                      'Correspondent.get_display_string() should return string containing date if date filled')
