from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import JobPosting, Application, Interview
from .serializers import (JobPostingSerializer, ApplicationSerializer, InterviewSerializer)

# Create your views here.

class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(company=self.request.user)


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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


# Ownership checks are commented out for now to facilitate testing, add back after creating employer user type
class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(
            Q(application__applicant=user)
        ).distinct()

    def perform_create(self, serializer):
        application = serializer.validated_data.get("application")

        """ ADD OWNERSHIP CHECK BACK LATER
        if application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to add an interview for this application.")
        """
        if application.status != "AP":
            raise PermissionDenied("You can only add an interview for an application that has been submitted.")
        application.status = "IN"
        application.save(update_fields=["status"])
        serializer.save()

    def perform_update(self, serializer):
        interview = self.get_object()

        """ ADD OWNERSHIP CHECK BACK LATER
        if interview.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to edit this interview.")
        """
        if interview.application.status != "IN":
            raise PermissionDenied("You can only update an interview for an application that is in interview stage.")
        serializer.save()

    def perform_destroy(self, instance):

        """ ADD OWNERSHIP CHECK BACK LATER
        if instance.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to delete this interview.")
        """
        application = instance.application
        instance.delete()
        # If no more interviews exist for this application, revert status back to AP
        if not Interview.objects.filter(application=application).exists():
            application.status = "AP"
            application.save(update_fields=["status"])