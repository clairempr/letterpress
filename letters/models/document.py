from django.db import models
from django_date_extensions.fields import ApproximateDateField
from tinymce import models as tinymce_models
from letters.models import Correspondent, DocumentImage, DocumentSource
from letters.models.util import get_image_preview

DEFAULT_LANGUAGE = 'EN'


class Document(models.Model):
    source = models.ForeignKey(DocumentSource)
    date = ApproximateDateField(default='', blank=True)
    writer = models.ForeignKey(Correspondent, related_name='%(model_name)s_writer')
    language = models.CharField(max_length=2, default=DEFAULT_LANGUAGE, blank=True)
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

    class Meta:
        abstract = True

