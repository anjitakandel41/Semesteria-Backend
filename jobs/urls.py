from django.urls import path

from jobs.views import JobListView

urlpatterns = [
    path('jobs/', JobListView.as_view(), name='jobs-list'),
]