import importlib

from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

# Normally Django settings should be imported as "from django.conf import settings"
# but here we need to import our settings module explicitly so we can manually reload it
import letterpress.settings


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
