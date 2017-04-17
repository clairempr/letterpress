"""letterpress URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from letters.views import home, letter_by_id, random_letter, export, letters_view, search, \
    logout_view, stats_view, get_stats, places_view, place_by_id, search_places

from django.contrib import admin

admin.autodiscover()

urlpatterns = [
                  url(r'^admin/', admin.site.urls),
                  url(r'^accounts/login/$', auth_views.login, name='login'),
                  url(r'^$', home, name='home'),
                  url(r'^accounts/logout/$', logout_view, name='logout'),
                  url(r'^export/', export, name='export'),
                  url(r'^letters/(?P<letter_id>[0-9]+)/$', letter_by_id, name='letter_by_id'),
                  url(r'^letters/', letters_view, name='letters_view'),
                  url(r'^search_places/', search_places, name='search_places'),
                  url(r'^search/', search, name='search'),
                  url(r'^random_letter/', random_letter, name='random_letter'),
                  url(r'^stats/', stats_view, name='stats_view'),
                  url(r'^get_stats/', get_stats, name='get_stats'),
                  url(r'^places/(?P<place_id>[0-9]+)/$', place_by_id, name='place_by_id'),
                  url(r'^places/', places_view, name='places'),
                  url(r'^tinymce/', include('tinymce.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
