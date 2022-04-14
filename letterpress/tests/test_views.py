from django.test import SimpleTestCase
from django.urls import reverse

from letterpress.views import HomeView


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
