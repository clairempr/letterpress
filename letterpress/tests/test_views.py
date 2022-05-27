from django.test import SimpleTestCase
from django.urls import reverse

from letterpress.views import ElasticsearchErrorView, HomeView


class HomeViewTestCase(SimpleTestCase):
    """
    Test HomeView
    """

    def test_get_context_data(self):
        """
        context_data should contain "title" and "nbar"
        """

        view = HomeView()
        context = view.get_context_data()
        self.assertEqual(context.get('title'), 'Letterpress', "'Letterpress' should be in context")
        self.assertEqual(context.get('nbar'), 'home', "nbar: home should be in context")

    def test_template_used(self):
        response = self.client.get(reverse('home'), follow=True)
        self.assertTemplateUsed(response, 'letterpress.html')


class ElasticsearchErrorViewTestCase(SimpleTestCase):
    """
    Test ElasticsearchErrorViewView
    """

    def test_get_context_data(self):
        """
        context_data should contain "title", "status_code", "status_description", and "error"
        """

        view = ElasticsearchErrorView()

        context = view.get_context_data()

        self.assertEqual(context.get('title'), 'Elasticsearch Error', "'Elasticsearch Error' should be in context")
        self.assertIn('status_code', "status_code should be in context")
        self.assertIn('status_description', context, "status_description should be in context")
        self.assertIn('error', "error should be in context")

    def test_template_used(self):
        response = self.client.get(reverse('elasticsearch_error',
                                           kwargs={'error': 'Something went wrong', 'status': 406}), follow=True)
        self.assertTemplateUsed(response, 'elasticsearch_error.html')

