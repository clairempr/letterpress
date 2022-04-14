"""letterpress URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from letters.views import letter_by_id, random_letter, export, LettersView, search, \
    logout_view, StatsView, get_stats, places_view, place_by_id, search_places, \
    sentiment_view, letter_sentiment_view, text_sentiment_view, get_text_sentiment, \
    wordcloud_view, get_wordcloud
from letterpress.views import HomeView

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
                  url(r'^admin/', admin.site.urls),
                  url(r'^accounts/login/$', auth_views.login, name='login'),
                  url(r'^$', HomeView.as_view(), name='home'),
                  url(r'^accounts/logout/$', logout_view, name='logout'),
                  url(r'^export/', export, name='export'),
                  url(r'^letters/(?P<letter_id>[0-9]+)/sentiment/(?P<sentiment_id>[0-9]+)/$',
                        letter_sentiment_view, name='letter_sentiment_view'),
                  url(r'^letters/(?P<letter_id>[0-9]+)/$', letter_by_id, name='letter_by_id'),
                  url(r'^letters/', LettersView.as_view(), name='letters_view'),
                  url(r'^search_places/', search_places, name='search_places'),
                  url(r'^search/', search, name='search'),
                  url(r'^random_letter/', random_letter, name='random_letter'),
                  url(r'^stats/', StatsView.as_view(), name='stats_view'),
                  url(r'^get_stats/', get_stats, name='get_stats'),
                  url(r'^sentiment/', sentiment_view, name='sentiment_view'),
                  url(r'^text_sentiment/', text_sentiment_view, name='text_sentiment_view'),
                  url(r'^get_text_sentiment/', get_text_sentiment, name='get_text_sentiment'),
                  url(r'^places/(?P<place_id>[0-9]+)/$', place_by_id, name='place_by_id'),
                  url(r'^places/', places_view, name='places'),
                  url(r'^tinymce/', include('tinymce.urls')),
                  url(r'^wordcloud_image.png', get_wordcloud, name='get_wordcloud'),
                  url(r'^wordcloud/', wordcloud_view, name='wordcloud_view'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
