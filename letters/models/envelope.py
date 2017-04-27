from django.db import models
from django_date_extensions.fields import ApproximateDateField
from tinymce import models as tinymce_models
from letters.models import Correspondent, DocumentImage, DocumentSource, Place
from letters.models.util import get_image_preview


class Envelope(models.Model):
    source = models.ForeignKey(DocumentSource)
    description = models.CharField(max_length=75, blank=True)
    date = ApproximateDateField(default='', blank=True)
    writer = models.ForeignKey(Correspondent, related_name='envelope_writer')
    origin = models.ForeignKey(Place, related_name='origin')
    recipient = models.ForeignKey(Correspondent, related_name='envelope_recipient')
    destination = models.ForeignKey(Place, related_name='destination')
    contents = tinymce_models.HTMLField(null=True, blank=True)
    notes = tinymce_models.HTMLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.get_display_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        if self.description:
            return self.description

        return str.format('{writer} to {recipient}{date}',
                          writer=self.writer,
                          recipient=self.recipient,
                          date=', ' + self.date if self.date else '')

    def image_preview(self):
        return get_image_preview(self)
