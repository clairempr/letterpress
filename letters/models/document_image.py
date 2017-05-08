from django.conf import settings
from django.db import models
from letters.models.util import DocType, get_choices, mark_safe


class DocumentImage(models.Model):
    description = models.CharField(max_length=75, blank=True)
    type = models.CharField(max_length=1, choices=get_choices(DocType))
    image_file = models.ImageField(upload_to='letter_images')

    def __str__(self):
        if self.description:
            return self.description
        else:
            return str.format('Image: {0}', str(self.image_file.name))

    def get_url(self):
        return settings.MEDIA_URL + self.image_file.name

    def image_tag(self):
        return self.image_preview_with_link(400)

    image_tag.short_description = 'Image'

    def thumbnail(self):
        return self.image_preview_with_link(100)

    def image_preview_with_link(self, height):
        if self.image_file:
            html = str.format('<a href="{0}"><img src="{1}" height="{2}" /></a>',
                              self.get_url(), self.get_url(), height)
            return mark_safe(html)
        else:
            return 'No image'
