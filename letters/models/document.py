from django.db import models
from django_date_extensions.fields import ApproximateDateField
from tinymce import models as tinymce_models
from letters.models import Correspondent, DocumentImage, DocumentSource
from letters.models.util import get_choices, get_image_preview, Language


class Document(models.Model):
    source = models.ForeignKey(DocumentSource)
    date = ApproximateDateField(default='', blank=True)
    writer = models.ForeignKey(Correspondent, related_name='%(model_name)s_writer')
    language = models.CharField(max_length=2, default=Language.ENGLISH, blank=True, choices=get_choices(Language))
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def get_display_string(self):
        return 'Define "get_display_string" in %(class)s'

    def __str__(self):
        return self.get_display_string()

    def to_string(self):
        return self.get_display_string()

    def image_preview(self):
        return get_image_preview(self)

    # return formatted date with separators and unknown elements filled with '?'
    def list_date(self):
        if not self.date:
            return '(Undated)'
        my_year = '{:0>4}'.format(self.date.year) if self.date.year else '????'
        my_month = '{:0>2}'.format(self.date.month) if self.date.month else '??'
        my_day = '{:0>2}'.format(self.date.day) if self.date.day else '??'
        return str.format('{0}-{1}-{2}', my_year, my_month, my_day)

    # return date in the format yyyymmdd with zeroes in unknown elements
    def sort_date(self):
        return str.format('{:0>4}{:0>2}{:0>2}', self.date.year, self.date.month, self.date.day)

    # return date in the format yyyy-MM-dd or yyyy-MM or yyyy for elasticsearch index
    def index_date(self):
        index_date = str.format('{:0>4}', self.date.year)
        if self.date.month:
            index_date += str.format('-{:0>2}', self.date.month)
        if self.date.day:
            index_date += str.format('-{:0>2}', self.date.day)
        return index_date

    class Meta:
        abstract = True

