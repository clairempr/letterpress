from django.db import models
from letters.models import DocumentImage
from letters.models.util import get_image_preview


class Correspondent(models.Model):
    last_name = models.CharField(max_length=50, blank=True)
    married_name = models.CharField(max_length=50, blank=True)
    first_names = models.CharField(max_length=75, blank=True)
    suffix = models.CharField(max_length=10, blank=True)
    aliases = models.CharField(max_length=75, blank=True)
    description = models.TextField(blank=True)
    images = models.ManyToManyField(DocumentImage, blank=True)

    def __str__(self):
        return self.get_display_string()

    def __lt__(self, other):
        return self.to_string() < other.to_string()

    def to_string(self):
        return self.get_display_string()

    def get_display_string(self):
        desc = str.format('{last_name}{comma}{first_names}{married_name}{suffix}',
                          last_name=self.last_name,
                          comma=', ' if self.last_name and self.first_names else '',
                          first_names=self.first_names,
                          married_name=' (' + self.married_name + ')' if self.married_name else '',
                          suffix=', ' + self.suffix if self.suffix else '')
        return desc

    def to_export_string(self):
        desc = str.format('{0} {1}', self.first_names, self.last_name)
        if self.suffix:
            desc += ', ' + self.suffix
        return desc

    def image_preview(self):
        return get_image_preview(self)