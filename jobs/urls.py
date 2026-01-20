from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobPostingViewSet, ApplicationViewSet, InterviewViewSet

router = DefaultRouter()
router.register(r'job-postings', JobPostingViewSet, basename='job-postings')
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'interviews', InterviewViewSet, basename='interviews')


urlpatterns = [
    path('', include(router.urls)),
]