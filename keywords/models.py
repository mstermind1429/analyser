from django.db import models


class DomainData(models.Model):
    domain = models.CharField(max_length=1024)
    keyword = models.CharField(max_length=128)
    position = models.IntegerField(
        default=0,
        null=True
    )
    url = models.CharField(
        max_length=1024,
        null=True
    )
    title = models.CharField(max_length=2048)
    traffic_index = models.IntegerField(
        default=0,
        null=True
    )
    search_volume = models.IntegerField(default=0)
    trend = models.IntegerField(default=0)
    integration = models.CharField(
        max_length=2048,
        default=None,
        null=True
    )
    cpc = models.FloatField(default=0.0)
    competition = models.FloatField(default=0.0)

    class Meta:
        verbose_name = 'Domain Data Keyword'
        unique_together = ('domain', 'keyword', 'url')

    def __str__(self):
        return self.keyword

