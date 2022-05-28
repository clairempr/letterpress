# Misc. enums and methods that are used with multiple model
from django.db.models import TextChoices
import django.db.models.options as options
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup


class DocType(TextChoices):
    LETTER = 'L'
    ENVELOPE = 'E'
    TRANSCRIPTION = 'T'
    OTHER = 'D'


class Language(TextChoices):
    ENGLISH = 'EN'
    DUTCH = 'NL'
    GERMAN = 'DE'


options.DEFAULT_NAMES += 'es_index_name', 'es_mapping'


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
