from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from applications.models import Application, ApplicationHistory
from jobs.models import Job


class HiringDashboardAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = 'StrongPass123!'

        self.candidate = User.objects.create_user(
            username='candidate1',
            email='candidate1@example.com',
            password=self.password,
            role=User.ROLE_CANDIDATE,
        )
        self.other_candidate = User.objects.create_user(
            username='candidate2',
            email='candidate2@example.com',
            password=self.password,
            role=User.ROLE_CANDIDATE,
        )
        self.recruiter1 = User.objects.create_user(
            username='recruiter1',
            email='recruiter1@example.com',
            password=self.password,
            role=User.ROLE_RECRUITER,
        )
        self.recruiter2 = User.objects.create_user(
            username='recruiter2',
            email='recruiter2@example.com',
            password=self.password,
            role=User.ROLE_RECRUITER,
        )

        self.job_open_a = Job.objects.create(
            title='Open Engineer Role',
            description='Open role for recruiter1',
            status=Job.STATUS_OPEN,
            assigned_recruiter=self.recruiter1,
        )
        self.job_open_b = Job.objects.create(
            title='Open Product Role',
            description='Open role for recruiter2',
            status=Job.STATUS_OPEN,
            assigned_recruiter=self.recruiter2,
        )
        self.job_closed = Job.objects.create(
            title='Closed Design Role',
            description='Closed role assigned to recruiter1',
            status=Job.STATUS_CLOSED,
            assigned_recruiter=self.recruiter1,
        )

    def login(self, user):
        response = self.client.post(
            reverse('auth-login'),
            {'username': user.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data['access']

    def test_candidate_can_apply_to_open_job(self):
        self.login(self.candidate)

        response = self.client.post(reverse('application-create'), {'job_id': self.job_open_a.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['job'], self.job_open_a.id)
        self.assertEqual(response.data['stage'], Application.STAGE_APPLIED)
        self.assertEqual(Application.objects.filter(candidate=self.candidate, job=self.job_open_a).count(), 1)

    def test_candidate_cannot_apply_to_closed_job(self):
        self.login(self.candidate)

        response = self.client.post(reverse('application-create'), {'job_id': self.job_closed.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Applications cannot be submitted to a closed job.')
        self.assertFalse(Application.objects.filter(candidate=self.candidate, job=self.job_closed).exists())

    def test_candidate_cannot_apply_twice_to_same_job(self):
        self.login(self.candidate)
        Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.post(reverse('application-create'), {'job_id': self.job_open_a.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['detail'], 'You have already applied to this job.')

    def test_database_prevents_duplicate_application(self):
        with self.assertRaises(IntegrityError):
            Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)
            Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

    def test_candidate_sees_only_their_own_applications(self):
        self.login(self.candidate)
        Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)
        Application.objects.create(candidate=self.other_candidate, job=self.job_open_b, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.get(reverse('applications-my'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['candidate'], self.candidate.username)

    def test_candidate_cannot_view_another_candidates_application(self):
        self.login(self.candidate)
        application = Application.objects.create(candidate=self.other_candidate, job=self.job_open_b, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.get(reverse('application-detail', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this application.')

    def test_candidate_can_withdraw_own_application(self):
        self.login(self.candidate)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.post(reverse('application-withdraw', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.STAGE_WITHDRAWN)
        self.assertEqual(application.version, 2)
        self.assertTrue(ApplicationHistory.objects.filter(application=application, new_stage=Application.STAGE_WITHDRAWN).exists())

    def test_candidate_cannot_withdraw_another_candidates_application(self):
        self.login(self.candidate)
        application = Application.objects.create(candidate=self.other_candidate, job=self.job_open_b, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.post(reverse('application-withdraw', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You can only withdraw your own application.')

    def test_recruiter_can_access_assigned_job_application(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.get(reverse('application-detail', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job'], self.job_open_a.id)

    def test_recruiter_cannot_access_unassigned_job_application(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_b, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.get(reverse('application-detail', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this application.')

    def test_valid_stage_transition_succeeds(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_SHORTLISTED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.STAGE_SHORTLISTED)
        self.assertEqual(application.version, 2)
        self.assertTrue(ApplicationHistory.objects.filter(application=application, previous_stage=Application.STAGE_APPLIED, new_stage=Application.STAGE_SHORTLISTED).exists())

    def test_invalid_stage_transition_fails(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_HIRED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid stage transition from APPLIED to HIRED.')
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.STAGE_APPLIED)
        self.assertEqual(application.version, 1)
        self.assertFalse(ApplicationHistory.objects.filter(application=application).exists())

    def test_skipping_stages_fails(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_INTERVIEWED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid stage transition from APPLIED to INTERVIEWED.')

    def test_terminal_stage_cannot_be_changed(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_HIRED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_REJECTED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('terminal', response.data['detail'])

    def test_successful_stage_change_creates_history(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_SHORTLISTED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        history = ApplicationHistory.objects.get(application=application)
        self.assertEqual(history.actor, self.recruiter1)
        self.assertEqual(history.previous_stage, Application.STAGE_APPLIED)
        self.assertEqual(history.new_stage, Application.STAGE_SHORTLISTED)

    def test_failed_stage_change_does_not_create_history(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)
        before_count = ApplicationHistory.objects.filter(application=application).count()

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_HIRED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ApplicationHistory.objects.filter(application=application).count(), before_count)

    def test_history_endpoint_exposes_actor_and_stage_changes(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)
        self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_SHORTLISTED, 'version': 1},
            format='json',
        )

        response = self.client.get(reverse('application-history', kwargs={'pk': application.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data[0]['actor'], self.recruiter1.username)
        self.assertEqual(response.data[0]['previous_stage'], Application.STAGE_APPLIED)
        self.assertEqual(response.data[0]['new_stage'], Application.STAGE_SHORTLISTED)

    def test_stale_version_returns_409_and_does_not_overwrite_stage(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)
        first_response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_SHORTLISTED, 'version': 1},
            format='json',
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_REJECTED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.STAGE_SHORTLISTED)
        self.assertEqual(application.version, 2)
        self.assertEqual(ApplicationHistory.objects.filter(application=application).count(), 1)

    def test_application_state_and_history_are_consistent_after_failed_transition(self):
        self.login(self.recruiter1)
        application = Application.objects.create(candidate=self.candidate, job=self.job_open_a, stage=Application.STAGE_APPLIED, version=1)

        response = self.client.patch(
            reverse('application-stage-change', kwargs={'pk': application.pk}),
            {'stage': Application.STAGE_HIRED, 'version': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        application.refresh_from_db()
        self.assertEqual(application.stage, Application.STAGE_APPLIED)
        self.assertEqual(application.version, 1)
        self.assertEqual(ApplicationHistory.objects.filter(application=application).count(), 0)
