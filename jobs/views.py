from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Profile, Company, JobPosting, Application, Interview
from .serializers import (JobPostingSerializer, ApplicationSerializer, InterviewSerializer)
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
            return Application.objects.filter(job__company=self.request.user.profile.company, status__in=["AP", "IN"])
        return Application.objects.filter(applicant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    def perform_update(self, serializer):
        application = self.get_object()
        if application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to edit this application.")
        if application.status != "DR":
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
    
    @action(detail=True, methods=["put"]) # Custom action to withdraw an application
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
        app.transition_status(Application.OF)
        return Response({"id": app.id, "status": app.status})
    
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        app = self.get_object()
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("No permission.")
        app.transition_status(Application.RE)
        return Response({"id": app.id, "status": app.status})
    
    

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
        application = serializer.validated_data.get("application")

        if application.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to create an interview for this application.")

        if application.status != "AP":
            raise PermissionDenied("You can only add an interview for an application that has been submitted.")
        application.status = "IN"
        application.save(update_fields=["status"])
        serializer.save()

    def perform_update(self, serializer):
        application = serializer.instance.application

        if application.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to update this interview.")
        
        if application.status != "IN":
            raise PermissionDenied("You can only update an interview for an application that is in interview stage.")
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        application = instance.application

        if application.job.company != self.request.user.profile.company or self.request.user.profile.company is None:
            raise PermissionDenied("You do not have permission to delete this interview.")

        instance.delete()
        # If no more interviews exist for this application, revert status back to AP
        if not Interview.objects.filter(application=application).exists():
            application.status = "AP"
            application.save(update_fields=["status"])

    @action(detail=True, methods=["post"])
    def offer(self, request, pk=None):
        interview = self.get_object()
        app = interview.application
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("No permission.")
        app.transition_status(Application.OF)
        return Response({"application_id": app.id, "status": app.status})
    
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        interview = self.get_object()
        app = interview.application
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("No permission.")
        app.transition_status(Application.RE)
        return Response({"application_id": app.id, "status": app.status})