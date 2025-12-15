from rest_framework import serializers
from .models import JobPosting, Application

class JobPostingSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobPosting
        fields = ['id', 'title', 'company_name', 'location', 'salary_range', 'description', 'posted_date', 'employment_type']

class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'application_date', 'status']