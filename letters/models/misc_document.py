from django.db import models
from tinymce import models as tinymce_models
from letters.models import Document, Envelope, Place
from letters.models.util import get_envelope_preview


class MiscDocument(Document):
    description = models.CharField(max_length=75)
    place = models.ForeignKey(Place)
    contents = tinymce_models.HTMLField(null=True, blank=True)
    envelopes = models.ManyToManyField(Envelope, blank=True)

    def get_display_string(self):
        return self.description

    def envelope_preview(self):
        return get_envelope_preview(self)

    class Meta:
        default_related_name = 'miscdoc'
