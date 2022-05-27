from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    """
    Renders the home page
    """

    template_name = 'letterpress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Letterpress'
        context['nbar'] = 'home'
        return context


class ElasticsearchErrorView(TemplateView):
    """
    Show Elasticsearch error message
    """

    template_name = 'elasticsearch_error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        status_code = kwargs.get('status', 0)
        status_descriptions = {
            400: '"Bad Request"',
            406: ''"Not Acceptable"''
        }

        if status_code in status_descriptions:
            status_description = status_descriptions[status_code]
        else:
            status_description = 'highly irregular'

        context['title'] = 'Elasticsearch Error'
        context['status_code'] = status_code
        context['status_description'] = status_description
        context['error'] = kwargs.get('error', '')
        return context
