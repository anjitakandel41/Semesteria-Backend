from rest_framework import serializers

from jobs.models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'status', 'assigned_recruiter', 'created_at', 'updated_at']
        read_only_fields = ['id', 'assigned_recruiter', 'created_at', 'updated_at']
