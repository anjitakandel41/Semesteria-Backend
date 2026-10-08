from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from accounts.models import User
from accounts.permissions import CanAccessApplication, IsCandidate, IsRecruiter
from applications.models import Application, ApplicationHistory
from applications.serializers import (
    ApplicationCreateRequestSerializer,
    ApplicationHistorySerializer,
    ApplicationSerializer,
    StageChangeRequestSerializer,
)
from applications.services import (
    ApplicationConflictError,
    change_application_stage,
    create_application,
    withdraw_application,
)
from jobs.models import Job


def _detail_from_exception(exc):
    if isinstance(exc, ValidationError):
        detail = exc.detail
        if isinstance(detail, dict):
            return detail.get('detail', str(detail))
        if isinstance(detail, list):
            return str(detail[0]) if detail else 'Invalid request.'
        return str(detail)
    if hasattr(exc, 'detail'):
        return str(exc.detail)
    return str(exc)


class ApplicationCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @swagger_auto_schema(
        operation_summary='Apply to an open job',
        request_body=ApplicationCreateRequestSerializer,
        responses={201: ApplicationSerializer},
    )
    def post(self, request, *args, **kwargs):
        job_id = request.data.get('job_id')
        if not job_id:
            return Response({'detail': 'job_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            application = create_application(request.user, job)
        except (ApplicationConflictError, ValidationError) as exc:
            return Response({'detail': _detail_from_exception(exc)}, status=409 if isinstance(exc, ApplicationConflictError) else 400)

        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @swagger_auto_schema(
        operation_summary='List my applications',
        responses={200: ApplicationSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        applications = Application.objects.filter(candidate=request.user).select_related('job').order_by('-created_at')
        return Response(ApplicationSerializer(applications, many=True).data)


class RecruiterApplicationListView(APIView):
    permission_classes = [IsAuthenticated, IsRecruiter]

    @swagger_auto_schema(
        operation_summary='List applications for my jobs',
        manual_parameters=[
            openapi.Parameter(
                'job_id',
                openapi.IN_QUERY,
                description='Filter by job ID',
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'stage',
                openapi.IN_QUERY,
                description='Filter by application stage',
                type=openapi.TYPE_STRING,
                enum=[value for value, _label in Application.STAGE_CHOICES],
            ),
        ],
        responses={200: ApplicationSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        job_id = request.query_params.get('job_id')
        stage = request.query_params.get('stage')
        queryset = Application.objects.filter(job__assigned_recruiter=request.user).select_related('job', 'candidate').order_by('-created_at')
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        if stage:
            queryset = queryset.filter(stage=stage)
        return Response(ApplicationSerializer(queryset, many=True).data)


class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Get application details',
        responses={200: ApplicationSerializer},
    )
    def get(self, request, *args, **kwargs):
        try:
            application = Application.objects.select_related('job', 'candidate', 'job__assigned_recruiter').get(pk=kwargs['pk'])
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not CanAccessApplication().has_object_permission(request, self, application):
            return Response({'detail': 'You do not have permission to access this application.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(ApplicationSerializer(application).data)


class WithdrawApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @swagger_auto_schema(
        operation_summary='Withdraw an application',
        request_body=None,
        responses={200: ApplicationSerializer},
    )
    def post(self, request, *args, **kwargs):
        try:
            application = Application.objects.select_related('candidate', 'job').get(pk=kwargs['pk'])
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.candidate != request.user:
            return Response({'detail': 'You can only withdraw your own application.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            updated_application = withdraw_application(request.user, application)
        except ValidationError as exc:
            return Response({'detail': _detail_from_exception(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ApplicationSerializer(updated_application).data, status=status.HTTP_200_OK)


class StageChangeView(APIView):
    permission_classes = [IsAuthenticated, IsRecruiter]

    @swagger_auto_schema(
        operation_summary='Update an application stage',
        request_body=StageChangeRequestSerializer,
        responses={200: ApplicationSerializer},
    )
    def patch(self, request, *args, **kwargs):
        try:
            application = Application.objects.select_related('job', 'job__assigned_recruiter').get(pk=kwargs['pk'])
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.job.assigned_recruiter != request.user:
            return Response({'detail': 'You do not have access to this application.'}, status=status.HTTP_403_FORBIDDEN)

        new_stage = request.data.get('stage')
        expected_version = request.data.get('version')
        if new_stage is None or expected_version is None:
            return Response({'detail': 'stage and version are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_app = change_application_stage(request.user, application, new_stage, int(expected_version))
        except ValidationError as exc:
            return Response({'detail': _detail_from_exception(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ApplicationConflictError as exc:
            return Response({'detail': _detail_from_exception(exc)}, status=exc.status_code)

        return Response(ApplicationSerializer(updated_app).data, status=status.HTTP_200_OK)


class ApplicationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Get application stage history',
        responses={200: ApplicationHistorySerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        try:
            application = Application.objects.select_related('job', 'job__assigned_recruiter', 'candidate').get(pk=kwargs['pk'])
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == User.ROLE_CANDIDATE and application.candidate != request.user:
            return Response({'detail': 'You do not have permission to access this application.'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == User.ROLE_RECRUITER and application.job.assigned_recruiter != request.user:
            return Response({'detail': 'You do not have permission to access this application.'}, status=status.HTTP_403_FORBIDDEN)

        history = ApplicationHistory.objects.filter(application=application).order_by('timestamp')
        return Response(ApplicationHistorySerializer(history, many=True).data)
