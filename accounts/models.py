from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CANDIDATE = 'candidate'
    ROLE_RECRUITER = 'recruiter'
    ROLE_CHOICES = [
        (ROLE_CANDIDATE, 'Candidate'),
        (ROLE_RECRUITER, 'Recruiter'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CANDIDATE)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['role'])]

    def __str__(self):
        return self.username
