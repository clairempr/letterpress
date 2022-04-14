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