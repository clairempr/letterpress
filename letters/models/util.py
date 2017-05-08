import django.db.models.options as options
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup
from enum import Enum


class DocType(Enum):
    LETTER = 'L'
    ENVELOPE = 'E'
    TRANSCRIPTION = 'T'
    OTHER = 'D'

options.DEFAULT_NAMES += 'es_index_name', 'es_type_name', 'es_mapping'


def get_envelope_preview(obj):
    return mark_safe('&nbsp;'.join([envelope.image_preview() for envelope in obj.envelopes.all()]))


def get_image_preview(obj):
    return mark_safe('&nbsp;'.join([image.image_tag() for image in obj.images.all()]))


def html_to_text(html):
    # Convert the html content into a beautiful soup object
    soup = BeautifulSoup(html,
                         'lxml')  # use 'lxml' instead of 'html.parser' for speed  # make sure we don't lose our line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    # Get plain text
    return soup.get_text()