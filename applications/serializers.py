from rest_framework import serializers

from applications.models import Application, ApplicationHistory
from jobs.models import Job


class ApplicationCreateRequestSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(min_value=1)


class StageChangeRequestSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=Application.STAGE_CHOICES)
    version = serializers.IntegerField(min_value=1)


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = serializers.StringRelatedField(read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    job_title = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'candidate', 'job', 'job_title', 'stage', 'version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'candidate', 'job', 'job_title', 'stage', 'version', 'created_at', 'updated_at']

    def get_job_title(self, obj):
        return obj.job.title


class ApplicationHistorySerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ApplicationHistory
        fields = ['id', 'application', 'actor', 'timestamp', 'previous_stage', 'new_stage']
        read_only_fields = ['id', 'application', 'actor', 'timestamp', 'previous_stage', 'new_stage']
