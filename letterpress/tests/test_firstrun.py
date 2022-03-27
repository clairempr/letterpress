from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase

from letterpress.firstrun import create_settings_secret, import_settings_secret, main


class FirstRunCase(SimpleTestCase):
    """
    firstrun.py should create a settings_secret.py file if it doesn't already exist
    """

    @patch('builtins.print', autospec=True)
    @patch('uuid.uuid4', autospec=True)
    @patch('builtins.open', autospec=True)
    def test_create_settings_secret(self, mock_open, mock_uuid4, mock_print):
        """
        create_settings_secret() should create a new settings_secret.py file
        """

        create_settings_secret()
        self.assertEqual(mock_print.call_count, 1, 'create_settings_secret() should call print()')
        self.assertEqual(mock_uuid4.call_count, 1, 'create_settings_secret() should call uuid4()')
        self.assertEqual(mock_open.call_count, 1, 'create_settings_secret() should call open()')

    def test_import_settings_secret(self):
        """
        This just imports settings_secret.py

        Since unit tests won't run locally if it's not there,
        just test that calling import_settings_secret() doesn't cause an error
        """

        import_settings_secret()

    @patch('letterpress.firstrun.import_settings_secret', autospec=True)
    @patch('letterpress.firstrun.create_settings_secret', autospec=True)
    def test_main(self, mock_create_settings_secret, mock_import_settings_secret):
        """
        If theres an ImportError when calling import_settings_secret(),
        create_settings_secret() should be called
        """

        # If there's no ImportError when calling import_settings_secret(),
        # create_settings_secret() should not be called
        mock_import_settings_secret.side_effect = None
        main()
        self.assertEqual(mock_create_settings_secret.call_count, 0,
                "If there's no ImportError from import_settings_secret(), create_settings_secret() shouldn't be called")

        # If there's an ImportError when calling import_settings_secret(),
        # create_settings_secret() should be called
        mock_import_settings_secret.side_effect = ImportError
        main()
        self.assertEqual(mock_create_settings_secret.call_count, 1,
                "If there's an ImportError from import_settings_secret(), create_settings_secret() should be called")
