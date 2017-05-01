from django.db import models
from django.contrib.gis.db import models

DEFAULT_COUNTRY = 'US'


class Place(models.Model):
    name = models.CharField(max_length=75, blank=True)
    state = models.CharField(max_length=2, blank=True)
    country = models.CharField(max_length=2, default=DEFAULT_COUNTRY, blank=True)
    # Geo Django field to store a point
    point = models.PointField(help_text='Represented as (longitude, latitude)', null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        desc = self.name
        if self.state:
            desc += ', ' + self.state
        if self.country != DEFAULT_COUNTRY:
            desc += ', ' + self.country
        return desc

    class Meta:
        ordering = ['name','state']