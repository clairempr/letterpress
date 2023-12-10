import importlib
import os

from unittest.mock import patch

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

        # If this is actually running under CircleCI,
        # don't check SECRET_KEY, ALLOWED_HOSTS, and ELASTICSEARCH_URL because there's no settings_secret
        # Just confirm that reading those settings with CIRCLECI set to False, will cause and AttributeError
        actually_circleci = letterpress.settings.CIRCLECI

        with patch.dict(os.environ, {'CIRCLECI': ''}):
            if actually_circleci:
                with self.assertRaises(AttributeError):
                    importlib.reload(letterpress.settings)
            else:
                # Really not running on CircleCI
                # Reload Django settings
                importlib.reload(letterpress.settings)

                # SECRET_KEY should NOT be 'super-duper-secret-key-for-circleci'
                self.assertNotEqual(
                    letterpress.settings.SECRET_KEY, 'super-duper-secret-key-for-circleci',
                    "When setting CIRCLECI isn't True, SECRET_KEY shouldn't be 'super-duper-secret-key-for-circleci'"
                )
                # ALLOWED_HOSTS should NOT be []
                self.assertNotEqual(letterpress.settings.ALLOWED_HOSTS, [],
                                    "When setting CIRCLECI isn't True, ALLOWED_HOSTS shouldn't be []")
                # ELASTICSEARCH_URL should have elasticsearch as host
                self.assertTrue('elasticsearch' in letterpress.settings.ELASTICSEARCH_URL,
                                "When setting CIRCLECI is True, ELASTICSEARCH_URL should contain 'elasticsearch'")

        # CIRCLECI environment variable set to True:
        with patch.dict(os.environ, {'CIRCLECI': 'true'}):
            # Reload Django settings
            importlib.reload(letterpress.settings)

            # SECRET_KEY should be 'super-duper-secret-key-for-circleci'
            self.assertEqual(
                letterpress.settings.SECRET_KEY, 'super-duper-secret-key-for-circleci',
                "When setting CIRCLECI is True, SECRET_KEY should be 'super-duper-secret-key-for-circleci'"
            )
            # ALLOWED_HOSTS should be []
            self.assertEqual(letterpress.settings.ALLOWED_HOSTS, [],
                             'When setting CIRCLECI is True, ALLOWED_HOSTS should be []')
            # ELASTICSEARCH_URL should have localhost as host
            self.assertTrue('localhost' in letterpress.settings.ELASTICSEARCH_URL,
                            "When setting CIRCLECI is True, ELASTICSEARCH_URL should contain 'localhost'")
