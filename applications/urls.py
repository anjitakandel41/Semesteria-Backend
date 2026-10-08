from django.urls import path

from applications.views import (
    ApplicationCreateView,
    ApplicationDetailView,
    ApplicationHistoryView,
    ApplicationListView,
    RecruiterApplicationListView,
    WithdrawApplicationView,
    StageChangeView,
)

urlpatterns = [
    path('applications/', ApplicationCreateView.as_view(), name='application-create'),
    path('applications/my/', ApplicationListView.as_view(), name='applications-my'),
    path('applications/<int:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<int:pk>/withdraw/', WithdrawApplicationView.as_view(), name='application-withdraw'),
    path('applications/<int:pk>/stage/', StageChangeView.as_view(), name='application-stage-change'),
    path('applications/<int:pk>/history/', ApplicationHistoryView.as_view(), name='application-history'),
    path('recruiter/applications/', RecruiterApplicationListView.as_view(), name='recruiter-applications'),
]