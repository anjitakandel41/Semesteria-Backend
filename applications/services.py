from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from accounts.models import User
from applications.models import Application, ApplicationHistory
from jobs.models import Job


class ApplicationConflictError(APIException):
    status_code = 409
    default_detail = 'Application was updated by another user. Please refresh and try again.'
    default_code = 'conflict'

    def __init__(self, detail=None, code=None):
        super().__init__(detail or self.default_detail, code or self.default_code)
        self.detail = detail or self.default_detail


class ApplicationPermissionError(APIException):
    status_code = 403
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'

    def __init__(self, detail=None, code=None):
        super().__init__(detail or self.default_detail, code or self.default_code)
        self.detail = detail or self.default_detail


VALID_TRANSITIONS = {
    Application.STAGE_APPLIED: {Application.STAGE_SHORTLISTED, Application.STAGE_REJECTED, Application.STAGE_WITHDRAWN},
    Application.STAGE_SHORTLISTED: {Application.STAGE_INTERVIEWED, Application.STAGE_REJECTED, Application.STAGE_WITHDRAWN},
    Application.STAGE_INTERVIEWED: {Application.STAGE_HIRED, Application.STAGE_REJECTED, Application.STAGE_WITHDRAWN},
}

TERMINAL_STAGES = {Application.STAGE_HIRED, Application.STAGE_REJECTED, Application.STAGE_WITHDRAWN}
WITHDRAWABLE_STAGES = {Application.STAGE_APPLIED, Application.STAGE_SHORTLISTED, Application.STAGE_INTERVIEWED}


def validate_stage_transition(current_stage, new_stage):
    if current_stage in TERMINAL_STAGES:
        raise ValidationError({"detail": f"Stage {current_stage} is terminal and cannot be changed."})
    if current_stage == new_stage:
        raise ValidationError({"detail": f"Stage is already {new_stage}."})
    allowed = VALID_TRANSITIONS.get(current_stage, set())
    if new_stage not in allowed:
        raise ValidationError({"detail": f"Invalid stage transition from {current_stage} to {new_stage}."})
    return True


def create_application(candidate, job):
    if candidate.role != User.ROLE_CANDIDATE:
        raise ApplicationPermissionError('Only candidates can apply to jobs.')
    if job.status != Job.STATUS_OPEN:
        raise ValidationError({"detail": 'Applications cannot be submitted to a closed job.'})
    if Application.objects.filter(candidate=candidate, job=job).exists():
        raise ApplicationConflictError('You have already applied to this job.')

    return Application.objects.create(
        candidate=candidate,
        job=job,
        stage=Application.STAGE_APPLIED,
        version=1,
    )


def withdraw_application(candidate, application):
    if application.candidate != candidate:
        raise ApplicationPermissionError('You can only withdraw your own application.')
    if application.stage not in WITHDRAWABLE_STAGES:
        raise ValidationError({"detail": 'This application cannot be withdrawn in its current stage.'})

    with transaction.atomic():
        current_stage = application.stage
        application.stage = Application.STAGE_WITHDRAWN
        application.version = application.version + 1
        application.save(update_fields=['stage', 'version', 'updated_at'])
        ApplicationHistory.objects.create(
            application=application,
            actor=candidate,
            previous_stage=current_stage,
            new_stage=Application.STAGE_WITHDRAWN,
        )
        return application


def change_application_stage(recruiter, application, new_stage, expected_version):
    if recruiter.role != User.ROLE_RECRUITER:
        raise ApplicationPermissionError('Only recruiters can update application stages.')
    if application.job.assigned_recruiter != recruiter:
        raise ApplicationPermissionError('You do not have access to this application.')

    validate_stage_transition(application.stage, new_stage)

    if application.version != expected_version:
        raise ApplicationConflictError(
            'Application was updated by another user. Please refresh and try again.'
        )

    with transaction.atomic():
        locked_application = Application.objects.select_for_update().get(pk=application.pk)
        if locked_application.version != expected_version:
            raise ApplicationConflictError(
                'Application was updated by another user. Please refresh and try again.'
            )
        previous_stage = locked_application.stage
        validate_stage_transition(previous_stage, new_stage)
        rows = Application.objects.filter(pk=locked_application.pk, version=expected_version).update(
            stage=new_stage,
            version=F('version') + 1,
            updated_at=timezone.now(),
        )
        if rows == 0:
            raise ApplicationConflictError(
                'Application was updated by another user. Please refresh and try again.'
            )
        locked_application.refresh_from_db()
        ApplicationHistory.objects.create(
            application=locked_application,
            actor=recruiter,
            previous_stage=previous_stage,
            new_stage=new_stage,
        )
        return locked_application
