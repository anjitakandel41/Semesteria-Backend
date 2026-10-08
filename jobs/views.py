from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from accounts.models import User
from jobs.models import Job
from jobs.serializers import JobSerializer


class JobListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='List available jobs',
        responses={200: JobSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        if request.user.role == User.ROLE_CANDIDATE:
            jobs = Job.objects.filter(status=Job.STATUS_OPEN).order_by('-created_at')
        else:
            jobs = Job.objects.all().order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)
