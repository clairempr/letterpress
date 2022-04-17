# Misc. enums and methods that are used with multiple models
import django.db.models.options as options
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup
from enum import Enum


def get_choices(enum):
    return ((choice.value, choice.name.title()) for choice in enum)


class DocType(Enum):
    LETTER = 'L'
    ENVELOPE = 'E'
    TRANSCRIPTION = 'T'
    OTHER = 'D'


class Language(Enum):
    ENGLISH = 'EN'
    DUTCH = 'NL'
    GERMAN = 'DE'


options.DEFAULT_NAMES += 'es_index_name', 'es_type_name', 'es_mapping'


def get_envelope_preview(obj):
    return mark_safe('&nbsp;'.join([envelope.image_preview() for envelope in obj.envelopes.all()]))


def get_image_preview(obj):
    return mark_safe('&nbsp;'.join(obj.image_tags()))


def html_to_text(html):
    """
    Convert the html content into a beautiful soup object
    """

    # use 'lxml' instead of 'html.parser' for speed
    soup = BeautifulSoup(html, 'lxml')
    # make sure we don't lose our line breaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    # Get plain text
    return soup.get_text()
