from django.db import models
from letters.models import DocumentImage
from letters.models.util import get_image_preview


class DocumentSource(models.Model):
    name = models.CharField(max_length=75, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def to_string(self):
        return self.name

    def image_preview(self):
        return get_image_preview(self)

    class Meta:
        ordering = ['name']