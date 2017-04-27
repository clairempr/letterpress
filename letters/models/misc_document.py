from django.db import models
from django_date_extensions.fields import ApproximateDateField
from tinymce import models as tinymce_models
from letters.models import Correspondent, DocumentImage, DocumentSource, Envelope, Place
from letters.models.util import get_image_preview


class MiscDocument(models.Model):
    source = models.ForeignKey(DocumentSource)
    description = models.CharField(max_length=75)
    date = ApproximateDateField(default='', blank=True)
    writer = models.ForeignKey(Correspondent, related_name='miscdoc_writer')
    place = models.ForeignKey(Place)
    contents = tinymce_models.HTMLField(null=True, blank=True)
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)
    envelopes = models.ManyToManyField(Envelope, blank=True)

    def __str__(self):
        return self.get_display_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        return self.description

    def image_preview(self):
        return get_image_preview(self)
