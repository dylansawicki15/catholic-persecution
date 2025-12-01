from django.db import models


class Martyr(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    date = models.DateField()
    source_url = models.URLField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Martyrs'

    def __str__(self):
        return f"{self.name} - {self.country} ({self.date})"


class PrayerIntention(models.Model):
    title = models.CharField(max_length=200)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Prayer Intentions'

    def __str__(self):
        return self.title
