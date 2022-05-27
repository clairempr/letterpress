from django.template.loader import render_to_string
from django.test import SimpleTestCase


class ErrorBaseTemplateTestCase(SimpleTestCase):
    """
    Test base error template
    """

    def test_template_content(self):
        template = 'error_base.html'
        rendered = render_to_string(template)

        self.assertIn('Oh dear! Error', rendered, "HTML should contain 'Oh dear! Error'")
        self.assertIn('spilled-ink.jpg', rendered, "HTML should contain 'spilled-ink.jpg'")
        self.assertIn('Your obedient servant', rendered, "HTML should contain 'Your obedient servant'")


class ErrorTemplateTestCase(object):
    """
    Base class for testing specific error pages
    This test doesn't actually get run
    """

    def setUp(self):
        self.template = ''
        self.code = ''
        self.description = ''

    def test_template_content(self):
        rendered = render_to_string(self.template)
        self.assertTrue(rendered.count(self.code) == 2,
                        'Status code {} should appear twice in rendered HTML'.format(self.code))
        self.assertIn(self.description, rendered,
                      'Status description {} should appear in rendered HTML'.format(self.description))


class Error400TemplateTestCase(ErrorTemplateTestCase, SimpleTestCase):
    """
    Test 400 error page page
    """

    def setUp(self):
        self.template = '400.html'
        self.code = '400'
        self.description = 'Bad Request'

    def test_template(self):
        self.test_template_content()


class Error403TemplateTestCase(ErrorTemplateTestCase, SimpleTestCase):
    """
    Test 403 error page page
    """

    def setUp(self):
        self.template = '403.html'
        self.code = '403'
        self.description = 'Forbidden'

    def test_template(self):
        self.test_template_content()


class Error404TemplateTestCase(ErrorTemplateTestCase, SimpleTestCase):
    """
    Test 404 error page page
    """

    def setUp(self):
        self.template = '404.html'
        self.code = '404'
        self.description = 'Not Found'

    def test_template(self):
        self.test_template_content()


class Error500TemplateTestCase(ErrorTemplateTestCase, SimpleTestCase):
    """
    Test 500 error page page
    """

    def setUp(self):
        self.template = '500.html'
        self.code = '500'
        self.description = 'Internal Server Error'

    def test_template(self):
        self.test_template_content()


class ElasticsearchErrorTemplateTestCase(SimpleTestCase):
    """
    Test Elasticsearch error template
    """

    def test_template_content(self):
        template = 'elasticsearch_error.html'

        rendered = render_to_string(template, context={'title': 'Elasticsearch Error',
                                                       'status_code': 406,
                                                       'status_description': 'highly irregular',
                                                       'error': 'Something went wrong'})

        self.assertIn('<title>Elasticsearch Error</title>', rendered, "HTML should contain title 'Elasticsearch Error'")
        self.assertIn('406', rendered, 'HTML should contain status code')
        self.assertIn('highly irregular', rendered, 'HTML should contain status description')
        self.assertIn('Something went wrong', rendered, 'HTML should contain error')
