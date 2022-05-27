"""letterpress URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from django.urls import path
from letters.views import GetStatsView, GetTextSentimentView, GetWordCloudView, LetterDetailView, \
    LetterSentimentView, LettersView, PlaceDetailView, PlaceListView, PlaceSearchView, RandomLetterView, \
    SearchView, SentimentView, StatsView, TextSentimentView, WordCloudView
from letterpress.views import ElasticsearchErrorView, HomeView

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('accounts/', include('django.contrib.auth.urls')),
                  path('', HomeView.as_view(), name='home'),
                  path('elasticsearch_error/<str:error>/<int:status>/', ElasticsearchErrorView.as_view(), name='elasticsearch_error'),
                  path('letters/<letter_id>/sentiment/<sentiment_id>/',
                       LetterSentimentView.as_view(), name='letter_sentiment_view'),
                  path('letters/<pk>/', LetterDetailView.as_view(), name='letter_detail'),
                  path('letters/', LettersView.as_view(), name='letters_view'),
                  path('search/', SearchView.as_view(), name='search'),
                  path('random_letter/', RandomLetterView.as_view(), name='random_letter'),
                  path('stats/', StatsView.as_view(), name='stats_view'),
                  path('get_stats/', GetStatsView.as_view(), name='get_stats'),
                  path('sentiment/', SentimentView.as_view(), name='sentiment_view'),
                  path('text_sentiment/', TextSentimentView.as_view(), name='text_sentiment_view'),
                  path('get_text_sentiment/', GetTextSentimentView.as_view(), name='get_text_sentiment'),
                  path('places/search/', PlaceSearchView.as_view(), name='place_search'),
                  path('places/<pk>/', PlaceDetailView.as_view(), name='place_detail'),
                  path('places/', PlaceListView.as_view(), name='place_list'),
                  path('tinymce/', include('tinymce.urls')),
                  path('wordcloud_image.png', GetWordCloudView.as_view(), name='get_wordcloud'),
                  path('wordcloud/', WordCloudView.as_view(), name='wordcloud_view'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
