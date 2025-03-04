# models.py
from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Observation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    observation_text = models.TextField()
    observation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Observation by {self.user.first_name} on {self.observation_date}"
