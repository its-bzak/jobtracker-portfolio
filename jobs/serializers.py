from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Interview, JobPosting, Application, Profile

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        profile = user.profile
        profile.account_type = Profile.ACCOUNT_APPLICANT
        profile.company = None
        profile.save(update_fields=["account_type", "company"])

        return user

class JobPostingSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobPosting
        fields = ['id', 'title', 'company', 'location', 'employment_means', 'salary_range', 'description', 'posted_date', 'employment_type']
        read_only_fields = ["id", "company", "posted_date"]
        
class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'notes', 'application_date', 'status']
        read_only_fields = ['id', 'applicant', 'job', 'application_date', 'status']

    def validate(self, data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Only drafts can be edited
        if self.instance and self.instance.status != "DR":
            raise serializers.ValidationError("You can only edit applications that are in Draft status.")

        job = data.get("job") or getattr(self.instance, "job", None) # Get job from data or instance
        if job is None:
            raise serializers.ValidationError({"job": "Job is required to create an application."})

        # Prevent duplicate applications on creation
        if self.instance is None:
            if Application.objects.filter(applicant=user, job=job).exists():
                raise serializers.ValidationError("You have already applied for this job.")

        return data
    
    def create(self, validated_data):
        request = self.context.get("request")
        validated_data['applicant'] = request.user
        return super().create(validated_data)
    
class InterviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interview
        fields = ['id', 'application', 'interview_date', 'interviewer_name', 'notes', 'means_of_interview']
        read_only_fields = ['id']

    def allowCreateOnlyForAuthorizedUsers(self, application, user):
        company = getattr(getattr(user, "profile", None), "company", None)
        if application.job.company != company or company is None: # Only employers associated with the job's company can create interviews
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
    
# Serializer for the authenticated user's own data
class MeSerializer(serializers.ModelSerializer):
    account_type = serializers.CharField(source="profile.account_type", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "account_type"]
        read_only_fields = ["id", "username", "email", "account_type"]