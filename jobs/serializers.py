from rest_framework import serializers
from .models import Interview, JobPosting, Application

class JobPostingSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobPosting
        fields = ['id', 'title', 'company', 'location', 'employment_means', 'salary_range', 'description', 'posted_date', 'employment_type']

class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'application_date', 'status']
        read_only_fields = ['id', 'applicant', 'status', 'application_date']

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        job = data.get("job") or getattr(self.instance, "job", None)
        applicant = data.get("applicant") or getattr(self.instance, "applicant", None) or user

        applicant = user

        qs = Application.objects.filter(applicant=applicant, job=job)

        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk) # Exclude the current instance when updating
            if qs.exists():
                raise serializers.ValidationError("You have already applied for this job.")

        return data
    
class InterviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interview
        fields = ['id', 'application', 'interview_date', 'interviewer_name', 'notes', 'means_of_interview']
        read_only_fields = ['id']

    def allowCreateOnlyForAuthorizedUsers(self, application, user):
        if application.job.company != user.profile.company: # Only employers associated with the job's company can create interviews
            raise serializers.ValidationError("You do not have permission to create an interview for this application.")
    def validate(self, data): # Ensure only one interview per application
        request = self.context.get("request")
        user = getattr(request, "user", None)

        application = data.get("application") or getattr(self.instance, "application", None)

        if self.instance is None: # Creation
            if Interview.objects.filter(application=application).exists():
                raise serializers.ValidationError("An interview for this application already exists.")
            self.allowCreateOnlyForAuthorizedUsers(application, user)
        else: # Update
            if application != self.instance.application:
                raise serializers.ValidationError("You cannot change the application of an existing interview.")

        return data