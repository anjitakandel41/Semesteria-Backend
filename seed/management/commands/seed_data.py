from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from applications.models import Application, ApplicationHistory
from jobs.models import Job


class Command(BaseCommand):
    help = 'Seed demo hiring dashboard data with candidate and recruiter accounts.'

    def handle(self, *args, **options):
        with transaction.atomic():
            candidate1, _ = User.objects.get_or_create(
                username='candidate1',
                defaults={
                    'email': 'candidate1@example.com',
                    'password': 'Candidate@123',
                    'role': User.ROLE_CANDIDATE,
                    'first_name': 'Candidate',
                    'last_name': 'One',
                },
            )
            candidate1.set_password('Candidate@123')
            candidate1.save(update_fields=['password'])

            candidate2, _ = User.objects.get_or_create(
                username='candidate2',
                defaults={
                    'email': 'candidate2@example.com',
                    'password': 'Candidate@456',
                    'role': User.ROLE_CANDIDATE,
                    'first_name': 'Candidate',
                    'last_name': 'Two',
                },
            )
            candidate2.set_password('Candidate@456')
            candidate2.save(update_fields=['password'])

            recruiter1, _ = User.objects.get_or_create(
                username='recruiter1',
                defaults={
                    'email': 'recruiter1@example.com',
                    'password': 'Recruiter@123',
                    'role': User.ROLE_RECRUITER,
                    'first_name': 'Recruiter',
                    'last_name': 'One',
                },
            )
            recruiter1.set_password('Recruiter@123')
            recruiter1.save(update_fields=['password'])

            recruiter2, _ = User.objects.get_or_create(
                username='recruiter2',
                defaults={
                    'email': 'recruiter2@example.com',
                    'password': 'Recruiter@456',
                    'role': User.ROLE_RECRUITER,
                    'first_name': 'Recruiter',
                    'last_name': 'Two',
                },
            )
            recruiter2.set_password('Recruiter@456')
            recruiter2.save(update_fields=['password'])

            # Rename the original demo jobs in place so existing applications keep
            # their job references when the seed command is upgraded.
            for old_title, new_title in (
                ('Open Job A', 'Full Stack Developer'),
                ('Open Job B', 'Data Analyst'),
            ):
                old_job = Job.objects.filter(title=old_title).first()
                new_job_exists = Job.objects.filter(title=new_title).exists()
                if old_job and not new_job_exists:
                    old_job.title = new_title
                    old_job.save(update_fields=['title'])

            job_a, _ = Job.objects.get_or_create(
                title='Full Stack Developer',
                defaults={
                    'description': 'Build and maintain web applications across frontend and backend services.',
                    'status': Job.STATUS_OPEN,
                    'assigned_recruiter': recruiter1,
                },
            )
            job_b, _ = Job.objects.get_or_create(
                title='Data Analyst',
                defaults={
                    'description': 'Analyze business data and build dashboards and reports for product teams.',
                    'status': Job.STATUS_OPEN,
                    'assigned_recruiter': recruiter2,
                },
            )
            job_c, _ = Job.objects.get_or_create(
                title='Closed Job C',
                defaults={
                    'description': 'A closed role assigned to recruiter1.',
                    'status': Job.STATUS_CLOSED,
                    'assigned_recruiter': recruiter1,
                },
            )

            additional_positions = [
                (
                    'Junior Software Developer',
                    'Help design, implement, test, and maintain software features with the engineering team.',
                    recruiter1,
                ),
                (
                    'Software Engineering Intern',
                    'Work with engineers on scoped software projects, code reviews, and automated tests.',
                    recruiter2,
                ),
                (
                    'Frontend Developer',
                    'Build accessible, responsive user interfaces and integrate them with backend APIs.',
                    recruiter1,
                ),
                (
                    'Backend Developer',
                    'Develop secure APIs, data models, and backend services for web applications.',
                    recruiter2,
                ),
                (
                    'QA Automation Engineer',
                    'Create and maintain automated tests to improve application quality and reliability.',
                    recruiter1,
                ),
            ]
            for title, description, recruiter in additional_positions:
                Job.objects.get_or_create(
                    title=title,
                    defaults={
                        'description': description,
                        'status': Job.STATUS_OPEN,
                        'assigned_recruiter': recruiter,
                    },
                )

            app_applied, _ = Application.objects.get_or_create(
                candidate=candidate1,
                job=job_b,
                defaults={'stage': Application.STAGE_APPLIED, 'version': 1},
            )

            app_shortlisted, _ = Application.objects.get_or_create(
                candidate=candidate1,
                job=job_a,
                defaults={'stage': Application.STAGE_SHORTLISTED, 'version': 2},
            )
            if app_shortlisted.history.count() == 0:
                ApplicationHistory.objects.create(
                    application=app_shortlisted,
                    actor=recruiter1,
                    previous_stage=Application.STAGE_APPLIED,
                    new_stage=Application.STAGE_SHORTLISTED,
                )

            app_interviewed, _ = Application.objects.get_or_create(
                candidate=candidate2,
                job=job_a,
                defaults={'stage': Application.STAGE_INTERVIEWED, 'version': 3},
            )
            if app_interviewed.history.count() == 0:
                ApplicationHistory.objects.create(
                    application=app_interviewed,
                    actor=recruiter1,
                    previous_stage=Application.STAGE_APPLIED,
                    new_stage=Application.STAGE_SHORTLISTED,
                )
                ApplicationHistory.objects.create(
                    application=app_interviewed,
                    actor=recruiter1,
                    previous_stage=Application.STAGE_SHORTLISTED,
                    new_stage=Application.STAGE_INTERVIEWED,
                )

            app_rejected, _ = Application.objects.get_or_create(
                candidate=candidate2,
                job=job_b,
                defaults={'stage': Application.STAGE_REJECTED, 'version': 2},
            )
            if app_rejected.history.count() == 0:
                ApplicationHistory.objects.create(
                    application=app_rejected,
                    actor=recruiter2,
                    previous_stage=Application.STAGE_APPLIED,
                    new_stage=Application.STAGE_REJECTED,
                )

            app_withdrawn, _ = Application.objects.get_or_create(
                candidate=candidate1,
                job=job_c,
                defaults={'stage': Application.STAGE_WITHDRAWN, 'version': 2},
            )
            if app_withdrawn.history.count() == 0:
                ApplicationHistory.objects.create(
                    application=app_withdrawn,
                    actor=candidate1,
                    previous_stage=Application.STAGE_INTERVIEWED,
                    new_stage=Application.STAGE_WITHDRAWN,
                )

            self.stdout.write(self.style.SUCCESS('Seed data created successfully.'))
