"""letterpress URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from letters.views import GetStatsView, GetTextSentimentView, GetWordCloudView, LetterDetailView, \
    LetterSentimentView, LettersView, logout_view, PlaceDetailView, PlaceListView, PlaceSearchView, RandomLetterView, \
    SearchView, SentimentView, StatsView, TextSentimentView, WordCloudView
from letterpress.views import HomeView

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
                  url(r'^admin/', admin.site.urls),
                  url(r'^accounts/login/$', auth_views.login, name='login'),
                  url(r'^$', HomeView.as_view(), name='home'),
                  url(r'^accounts/logout/$', logout_view, name='logout'),
                  url(r'^letters/(?P<letter_id>[0-9]+)/sentiment/(?P<sentiment_id>[0-9]+)/$',
                        LetterSentimentView.as_view(), name='letter_sentiment_view'),
                  url(r'^letters/(?P<pk>[0-9]+)/$', LetterDetailView.as_view(), name='letter_detail'),
                  url(r'^letters/', LettersView.as_view(), name='letters_view'),
                  url(r'^search/', SearchView.as_view(), name='search'),
                  url(r'^random_letter/', RandomLetterView.as_view(), name='random_letter'),
                  url(r'^stats/', StatsView.as_view(), name='stats_view'),
                  url(r'^get_stats/', GetStatsView.as_view(), name='get_stats'),
                  url(r'^sentiment/', SentimentView.as_view(), name='sentiment_view'),
                  url(r'^text_sentiment/', TextSentimentView.as_view(), name='text_sentiment_view'),
                  url(r'^get_text_sentiment/', GetTextSentimentView.as_view(), name='get_text_sentiment'),
                  url(r'^places/search/', PlaceSearchView.as_view(), name='place_search'),
                  url(r'^places/(?P<pk>[0-9]+)/$', PlaceDetailView.as_view(), name='place_detail'),
                  url(r'^places/', PlaceListView.as_view(), name='place_list'),
                  url(r'^tinymce/', include('tinymce.urls')),
                  url(r'^wordcloud_image.png', GetWordCloudView.as_view(), name='get_wordcloud'),
                  url(r'^wordcloud/', WordCloudView.as_view(), name='wordcloud_view'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
