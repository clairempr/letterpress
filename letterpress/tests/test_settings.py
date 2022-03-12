import importlib
import os

from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

# Normally Django settings should be imported as "from django.conf import settings"
# but here we need to import our settings module explicitly so we can manually reload it
import letterpress.settings


class TestCircleCISettingsTestCase(SimpleTestCase):
    """
    Some settings should be different under CircleCI
    """

    def test_circleci_settings(self):
        # CIRCLECI environment variable not set to True:

        # If this is actually running under CircleCI, don't check SECRET_KEY and ALLOWED_HOSTS,
        # because there's no settings_secret
        actually_circleci = letterpress.settings.CIRCLECI

        with patch.dict(os.environ, {'CIRCLECI': ''}):
            if actually_circleci:
                self.assertRaises(AttributeError, importlib.reload, letterpress.settings)


            # If actually running on CircleCI but setting CIRCLECI is false,
            # the values SECRET_KEY and ALLOWED_HOSTS should be different
            if actually_circleci:
                self.assertRaises(AttributeError, letterpress.settings.SECRET_KEY)
                # SECRET_KEY should NOT be 'super-duper-secret-key-for-circleci'
                self.assertNotEqual(letterpress.settings.SECRET_KEY, 'SECRET_SETTINGS not in settings_secret',
                    "When running on CircleCI but setting CIRCLECI isn't True, SECRET_KEY should be 'SECRET_SETTINGS not in settings_secret'")
                # ALLOWED_HOSTS should NOT be []
                self.assertNotEqual(letterpress.settings.ALLOWED_HOSTS, [],
                    "When running on CircleCI but setting CIRCLECI isn't True, ALLOWED_HOSTS should be 'ALLOWED_HOSTS not in settings_secret'")
            else:
                # Really not running on CircleCI
                # Reload Django settings
                importlib.reload(letterpress.settings)

                # SECRET_KEY should NOT be 'super-duper-secret-key-for-circleci'
                self.assertNotEqual(letterpress.settings.SECRET_KEY, 'super-duper-secret-key-for-circleci',
                            "When setting CIRCLECI isn't True, SECRET_KEY shouldn't be 'super-duper-secret-key-for-circleci'")
                # ALLOWED_HOSTS should NOT be []
                self.assertNotEqual(letterpress.settings.ALLOWED_HOSTS, [],
                                    "When setting CIRCLECI isn't True, ALLOWED_HOSTS shouldn't be []")
            # Maybe running on CircleCI, maybe locally
            # ELASTICSEARCH_URL should have elasticsearch as host
            self.assertTrue('elasticsearch' in letterpress.settings.ELASTICSEARCH_URL,
                            "When setting CIRCLECI is True, ELASTICSEARCH_URL should contain 'elasticsearch'")

        # CIRCLECI environment variable set to True:
        with patch.dict(os.environ, {'CIRCLECI': 'true'}):
            # Reload Django settings
            importlib.reload(letterpress.settings)

            # SECRET_KEY should be 'super-duper-secret-key-for-circleci'
            self.assertEqual(letterpress.settings.SECRET_KEY, 'super-duper-secret-key-for-circleci',
                            "When setting CIRCLECI is True, SECRET_KEY should be 'super-duper-secret-key-for-circleci'")
            # ALLOWED_HOSTS should be []
            self.assertEqual(letterpress.settings.ALLOWED_HOSTS, [],
                             'When setting CIRCLECI is True, ALLOWED_HOSTS should be []')
            # ELASTICSEARCH_URL should have localhost as host
            self.assertTrue('localhost' in letterpress.settings.ELASTICSEARCH_URL,
                            "When setting CIRCLECI is True, ELASTICSEARCH_URL should contain 'localhost'")


class TestGeoDjangoSettingsTestCase(SimpleTestCase):
    """
    SPATIALITE_LIBRARY_PATH and GDAL_LIBRARY_PATH settings
    should be different for Linux and Windows
    """

    @patch('platform.system', autospec=True)
    def test_settings_for_linux(self, mock_system):
        """
        GDAL_LIBRARY_PATH should be set for Windows only
        If platform.system() returns something else, settings.GDAL_LIBRARY_PATH shouldn't be set
        """

        # Mock platform.system() to have it return 'Linux'
        mock_system.return_value = 'Linux'

        # Reload Django settings
        importlib.reload(letterpress.settings)

        self.assertTrue(letterpress.settings.SPATIALITE_LIBRARY_PATH.endswith('.so'),
                        "On Linux, SPATIALITE_LIBRARY_PATH should end with '.so'")

        with self.assertRaises(AttributeError):
            print(letterpress.settings.GDAL_LIBRARY_PATH)

    @patch('platform.system', autospec=True)
    def test_settings_for_windows(self, mock_system):
        """
        GDAL_LIBRARY_PATH should be set for Windows only
        If platform.system() returns 'Windows', settings.GDAL_LIBRARY_PATH should be set
        """

        # Mock platform.system() to have it return 'Windows'
        mock_system.return_value = 'Windows'

        # Reload Django settings
        importlib.reload(letterpress.settings)

        self.assertFalse(letterpress.settings.SPATIALITE_LIBRARY_PATH.endswith('.so'),
                         "On Windows, SPATIALITE_LIBRARY_PATH should not end with '.so'")

        self.assertFalse(letterpress.settings.GDAL_LIBRARY_PATH == None,
                         'On Windows, GDAL_LIBRARY_PATH should be set')
