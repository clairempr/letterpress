from django_date_extensions.fields import ApproximateDate
from elasticsearch import Elasticsearch
from unittest import skip
from unittest.mock import patch

from django.test import TestCase

from letters import es_settings
from letters.management.commands.push_to_index import Command
from letters.models import Letter
from letters.tests.factories import LetterFactory


class PushToIndexTestCase(TestCase):
    """
    push_to_index() should populate Elasticsearch index with Letters
    """

    def recreate_test_index(self):
        indices_client = es_settings.ES_CLIENT.indices
        index_name = Letter._meta.es_index_name
        if indices_client.exists(index=index_name):
            indices_client.delete(index=index_name)
        indices_client.create(index=index_name,
                              body={'settings': es_settings.settings})

    def setUp(self):
        self.command = Command()
        self.letter = LetterFactory(date=ApproximateDate(1862, 1, 1),
                                    body='As this is the beginin of a new year I thought as I was a lone to night I '
                                         'would write you a few lines to let you know that we are not all ded yet.')

    @patch.object(Command, 'recreate_index', autospec=True)
    @patch.object(Command, 'push_db_to_index', autospec=True)
    def test_handle(self, mock_push_db_to_index, mock_recreate_index):
        """
        Command.handle() should call Command.recreate_index() and Command.push_db_to_index()
        """

        self.command.handle()

        self.assertEqual(mock_recreate_index.call_count, 1, 'Command.handle() should call Command.recreate_index()')
        self.assertEqual(mock_push_db_to_index.call_count, 1, 'Command.handle() should call Command.push_db_to_index()')

    @patch('elasticsearch.client.IndicesClient.exists', autospec=True)
    @patch('elasticsearch.client.IndicesClient.delete', autospec=True)
    @patch('elasticsearch.client.IndicesClient.create', autospec=True)
    @patch('elasticsearch.client.IndicesClient.put_mapping', autospec=True)
    def test_recreate_index_with_mocks(self, mock_IndicesClient_put_mapping, mock_IndicesClient_create,
                                       mock_IndicesClient_delete, mock_IndicesClient_exists):
        """
        Command.recreate_index() should delete the Elasticsearch index if it exists, create a new one,
        and set up a mapping

        Unit test: mock everything
        """

        mock_IndicesClient_exists.return_value = True
        self.command.recreate_index()

        self.assertEqual(mock_IndicesClient_exists.call_count, 1,
                         'Command.recreate_index() should call IndicesClient.exists()')

        # If index exists, recreate_index() should call IndicesClient.delete()
        self.assertEqual(mock_IndicesClient_delete.call_count, 1,
                         'Command.recreate_index() should call IndicesClient.delete() if index exists')
        self.assertEqual(mock_IndicesClient_create.call_count, 1,
                         'Command.recreate_index() should call IndicesClient.create()')
        self.assertEqual(mock_IndicesClient_put_mapping.call_count, 1,
                         'Command.recreate_index() should call IndicesClient.put_mapping()')

        # If index doesn't exist, recreate_index() shouldn't call IndicesClient.delete()
        mock_IndicesClient_delete.reset_mock()
        mock_IndicesClient_exists.return_value = False
        self.command.recreate_index()
        self.assertEqual(mock_IndicesClient_delete.call_count, 0,
                         "Command.recreate_index() shouldn't call IndicesClient.delete() if index doesn't exist")

    # We don't want to be messing with the real Elasticsearch index
    @patch('letters.models.Letter._meta.es_index_name', 'letterpress_test')
    def test_push_db_to_index(self):
        self.recreate_test_index()

        # Just make sure this doesn't cause an error
        self.command.push_db_to_index()

    # We don't want to be messing with the real Elasticsearch index
    @patch('letters.models.Letter._meta.es_index_name', 'letterpress_test')
    def test_convert_for_bulk(self):
        """
        convert_for_bulk() should add keys and values to data
        """
        data = self.command.convert_for_bulk(self.letter)
        self.assertEqual(data.get('_id'), self.letter.pk,
                         'Data returned from convert_for_bulk() should contain letter id')
        self.assertEqual(data.get('contents'), self.letter.contents(),
                         'Data returned from convert_for_bulk() should contain letter contents')
        for key in ['date', 'source', 'writer', 'place']:
            self.assertIn(key, data, "Data returned from convert_for_bulk() should contain '{}'".format(key))
        self.assertEqual(data.get('_index'), Letter._meta.es_index_name,
                         'Data returned from convert_for_bulk() should contain letter index name')

