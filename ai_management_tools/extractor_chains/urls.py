from django.urls import path
from extractor_chains.resume_extractor import ResumeInfoAPIView

urlpatterns = [
    path('resumeInfoExtract', ResumeInfoAPIView.as_view()),
]