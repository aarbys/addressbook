from django.db import models


class Person(models.Model):
    Name = models.CharField(max_length=255)
    Inside = models.IntegerField(unique=True)
    Email = models.CharField(max_length=255)
    Corporation = models.CharField(max_length=255)
    Role = models.CharField(max_length=255)
    Subdivision = models.CharField(max_length=255)
    Outside = models.CharField(max_length=255)

    def __str__(self):
        return self.Name
