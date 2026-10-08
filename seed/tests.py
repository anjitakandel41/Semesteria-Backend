from django.core.management import call_command
from django.test import TestCase

from applications.models import Application
from jobs.models import Job


class SeedDataTests(TestCase):
    def test_seed_data_creates_it_positions_idempotently(self):
        expected_titles = {
            'Full Stack Developer',
            'Junior Software Developer',
            'Software Engineering Intern',
            'Data Analyst',
            'Frontend Developer',
            'Backend Developer',
            'QA Automation Engineer',
        }

        call_command('seed_data', verbosity=0)
        call_command('seed_data', verbosity=0)

        seeded_open_jobs = Job.objects.filter(
            title__in=expected_titles,
            status=Job.STATUS_OPEN,
        )
        self.assertSetEqual(
            set(seeded_open_jobs.values_list('title', flat=True)),
            expected_titles,
        )
        self.assertEqual(seeded_open_jobs.count(), len(expected_titles))
        self.assertTrue(Job.objects.filter(title='Closed Job C', status=Job.STATUS_CLOSED).exists())

        applications = list(Application.objects.select_related('job').all())
        self.assertSetEqual(
            {application.stage for application in applications},
            {
                'APPLIED',
                'SHORTLISTED',
                'INTERVIEWED',
                'HIRED',
                'REJECTED',
                'WITHDRAWN',
            },
        )
