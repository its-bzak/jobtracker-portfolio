from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from .models import Profile, JobPosting, Application, Interview, JobAppQuestion, JobAppAnswer
from .serializers import (JobPostingSerializer, ApplicationSerializer, InterviewSerializer, 
                          JobAppAnswerSerializer, JobAppQuestionSerializer)
from django.db import transaction

# Create your views here.

class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if profile.account_type != Profile.ACCOUNT_EMPLOYER or profile.company is None:
            raise PermissionDenied("Only employers with a company can create job postings.")
        serializer.save(company=profile.company)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.account_type == Profile.ACCOUNT_EMPLOYER:
            # Employers can see all submitted applications for their company's job postings
            return Application.objects.filter(job__company=self.request.user.profile.company, status__in=["AP", "IN", "RE", "OF"])
        return Application.objects.filter(applicant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    def perform_update(self, serializer):
        application = self.get_object()
        if application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to edit this application.")
        if application.status != Application.DR: # Only allow editing draft applications
            raise PermissionDenied("You can only edit draft applications.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to delete this application.")
        instance.delete()

    @action(detail=True, methods=["post"]) # Create a custom action to submit an application
    def submit(self, request, pk=None):
        application = self.get_object()

        # explicit application ownership check
        if application.applicant != request.user:
            raise PermissionDenied("You do not have permission to submit this application.")

        # only allow submit once
        if application.status != "DR":
            return Response(
                {"detail": "Only draft applications can be submitted."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        # To Do: Add any additional submission logic here (e.g., send notification, etc.)

        # To Do: Add required fields here (resume, cover letter, etc.)

        application.status = "AP" # mark as applied
        application.save(update_fields=["status"]) # only update status field

        return Response(
            {"id": application.id, "status": application.status},
            status=http_status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["post"]) # Custom action to withdraw an application
    def withdraw(self, request, pk=None):
        application = self.get_object()

        # explicit application ownership check
        if application.applicant != request.user:
            raise PermissionDenied("You do not have permission to withdraw this application.")

        # only allow withdraw if applied
        if application.status != "AP":
            return Response(
                {"detail": "Only submitted applications can be withdrawn."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        application.status = "DR" # revert back to draft
        application.save(update_fields=["status"]) # only update status field

        return Response(
            {"id": application.id, "status": application.status},
            status=http_status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["post"])
    def offer(self, request, pk=None):  
        app = self.get_object()
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("No permission.")
        try:
            app.transition_status(Application.OF) # try to mark as offered from applied
        except ValidationError as e: # catch any validation errors
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST) # return error message and status code
        
        return Response({"id": app.id, "status": app.status}) # return updated application status
    
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        app = self.get_object()
        try:
            app.transition_status(Application.RE) # try to mark as rejected from applied
        except ValidationError as e: # catch any validation errors
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST) # return error message and status code
        return Response({"id": app.id, "status": app.status}) # return updated application status
    
    @action(detail=True, methods=["post"])
    def promote_to_interview(self, request, pk=None):
        app = self.get_object()
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to promote this application.")
        try:
            app.transition_status(Application.IN) # mark as in interview from applied
        except ValidationError as e:
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST)
        
        return Response({"id": app.id, "status": app.status}, status=http_status.HTTP_200_OK)

# Ownership checks are commented out for now to facilitate testing, add back after creating employer user type
class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.account_type == Profile.ACCOUNT_EMPLOYER:
            return Interview.objects.filter(application__job__company=self.request.user.profile.company)
        return Interview.objects.filter(application__applicant=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        application = serializer.validated_data["application"]

        company = getattr(self.request.user.profile, "company", None)
        if company is None or application.job.company != company:
            raise PermissionDenied("You do not have permission to create an interview for this application.")

        if application.status != Application.IN: # Only allow scheduling an interview if the application is in Interview stage
            raise PermissionDenied("You can only schedule an interview once the application is in Interview stage.")

        serializer.save()

    def perform_update(self, serializer):
        application = serializer.instance.application

        if application.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to update this interview.")

        if application.status != Application.IN: # Only allow updating an interview if the application is in Interview stage
            raise PermissionDenied("You can only update an interview for an application that is in interview stage.")
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        application = instance.application

        if application.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to delete this interview.")

        instance.delete()

    @action(detail=True, methods=["post"])
    def offer(self, request, pk=None):
        interview = self.get_object()
        app = interview.application
        try:
            app.transition_status(Application.OF)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST)
        
        return Response({"id": app.id, "status": app.status})
    
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        interview = self.get_object()
        app = interview.application
        try:
            app.transition_status(Application.RE)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response({"id": app.id, "status": app.status})

class JobAppQuestionViewSet(viewsets.ModelViewSet):
    queryset = JobAppQuestion.objects.all()
    serializer_class = JobAppQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.account_type == Profile.ACCOUNT_EMPLOYER:
            return JobAppQuestion.objects.filter(job__company=self.request.user.profile.company)
        return JobAppQuestion.objects.none()  # Applicants cannot view questions directly

    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        if job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to add questions to this job posting.")
        serializer.save()

    def perform_update(self, serializer):
        question = self.get_object()
        if question.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to update this question.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to delete this question.")
        instance.delete()


class JobAppAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppAnswerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobAppAnswer.objects.filter(application__applicant=self.request.user)

    def perform_create(self, serializer):
        application = serializer.validated_data["application"]
        question = serializer.validated_data["question"]

        if application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to answer questions for this application.")

        if question.job != application.job:
            raise ValidationError("This question does not belong to the job posting for this application.")

        serializer.save()

    def perform_update(self, serializer):
        answer = self.get_object()
        if answer.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to update this answer.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to delete this answer.")
        instance.delete()