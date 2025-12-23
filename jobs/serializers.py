from rest_framework import serializers
from .models import Interview, JobPosting, Application, JobAppAnswer, JobAppQuestion

class JobPostingSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobPosting
        fields = ['id', 'title', 'company', 'location', 'employment_means', 'salary_range', 'description', 'posted_date', 'employment_type']

class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'job', 'application_date', 'status']
        read_only_fields = ['id', 'applicant', 'application_date', 'status']

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
    
# Eventually add views validation
class JobAppQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAppQuestion
        fields = ['id', 'job', 'question_prompt', 'answer_type']
        read_only_fields = ['id']

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        profile = user.profile

        if self.instance: # Check to see if question already exists
            job = self.instance.job
            if "job" in data and data["job"] != self.instance.job:
                raise serializers.ValidationError({"job": "You cannot change the job of an existing question."})
        else: # Go to create question if no match
            job = data.get("job")
            if job is None: # Job not found (needed)
                raise serializers.ValidationError({"job": "Cannot create a question without a job."})

        if (profile.account_type != profile.ACCOUNT_EMPLOYER or profile.company is None or profile.company != job.company):
            raise serializers.ValidationError("Only employers can create application questions for their company.")
        return data # Return created question for given job

class JobAppAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAppAnswer
        fields=['id', 'application', 'question', 'answer_value']
        read_only_fields=['id']
        
    def validate(self, data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if self.instance:
            application = self.instance.application
            question = self.instance.question

            if 'application' in data and data['application'] != application:
                raise serializers.ValidationError({"application": 'Cannot change application of an existing answer.'})
            if 'question' in data and data['question'] != question:
                raise serializers.ValidationError({'question': 'Cannot change question of an existing answer.'})
            
        else:
            application = data.get('application')
            question = data.get('question')
            if application is None:
                raise serializers.ValidationError({'application': 'Application is required.'})
            if question is None:
                raise serializers.ValidationError({'question': 'Question is required.'})
            
        if user is None or application.applicant != user:
            raise serializers.ValidationError('You do not have permission to answer questions for this application.')

        if application.status != Application.DR:
            raise serializers.ValidationError('You can only edit answers while the application is a draft.')

        if question.job_id != application.job_id:
            raise serializers.ValidationError({'question': 'This question does not belong to the correct job posting.'})
        
        return data
    