from django.conf import settings
from django.db import models


class Application(models.Model):
    STAGE_APPLIED = 'APPLIED'
    STAGE_SHORTLISTED = 'SHORTLISTED'
    STAGE_INTERVIEWED = 'INTERVIEWED'
    STAGE_HIRED = 'HIRED'
    STAGE_REJECTED = 'REJECTED'
    STAGE_WITHDRAWN = 'WITHDRAWN'
    STAGE_CHOICES = [
        (STAGE_APPLIED, 'Applied'),
        (STAGE_SHORTLISTED, 'Shortlisted'),
        (STAGE_INTERVIEWED, 'Interviewed'),
        (STAGE_HIRED, 'Hired'),
        (STAGE_REJECTED, 'Rejected'),
        (STAGE_WITHDRAWN, 'Withdrawn'),
    ]

    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_APPLIED)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['candidate', 'job'], name='unique_candidate_job_application'),
        ]
        indexes = [
            models.Index(fields=['candidate', 'job']),
            models.Index(fields=['job', 'stage']),
            models.Index(fields=['stage']),
            models.Index(fields=['version']),
        ]

    def __str__(self):
        return f'{self.candidate.username} -> {self.job.title}'


class ApplicationHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application_actions')
    timestamp = models.DateTimeField(auto_now_add=True)
    previous_stage = models.CharField(max_length=20, choices=Application.STAGE_CHOICES)
    new_stage = models.CharField(max_length=20, choices=Application.STAGE_CHOICES)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.application_id}: {self.previous_stage} -> {self.new_stage}'
