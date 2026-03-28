from django.urls import path

from .views import CreateJobView, DownloadStemView, HealthView, JobDetailView, MixStemView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("jobs/", CreateJobView.as_view(), name="create-job"),
    path("jobs/<uuid:job_id>/", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:job_id>/download/<str:stem>/", DownloadStemView.as_view(), name="download-stem"),
    path("jobs/<uuid:job_id>/mix/", MixStemView.as_view(), name="mix-stems"),
]
