from django.db import models
from tinymce import models as tinymce_models
from letters.models import Correspondent, Document, Place


class Envelope(Document):
    description = models.CharField(max_length=75, blank=True)
    origin = models.ForeignKey(Place, related_name='origin')
    recipient = models.ForeignKey(Correspondent, related_name='envelope_recipient')
    destination = models.ForeignKey(Place, related_name='destination')
    contents = tinymce_models.HTMLField(null=True, blank=True)

    def get_display_string(self):
        if self.description:
            return self.description

        return str.format('{writer} to {recipient}{date}',
                          writer=self.writer,
                          recipient=self.recipient,
                          date=', ' + str(self.date) if self.date else '')
