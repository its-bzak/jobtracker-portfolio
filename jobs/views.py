from urllib import request
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from .models import Profile, JobPosting, Application, Interview, JobAppQuestion, JobAppAnswer
from .serializers import (JobPostingSerializer, ApplicationSerializer, InterviewSerializer, 
                          JobAppAnswerSerializer, JobAppQuestionSerializer, RegisterSerializer)
from django.db import transaction
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "User registered successfully."}, status=http_status.HTTP_201_CREATED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=http_status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=http_status.HTTP_400_BAD_REQUEST)

class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if profile.account_type != Profile.ACCOUNT_EMPLOYER or profile.company is None:
            raise PermissionDenied("Only employers with a company can create job postings.")
        serializer.save(company=profile.company)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def apply(self, request, pk=None):
        job = self.get_object()
        profile = request.user.profile

        if profile.account_type != Profile.ACCOUNT_APPLICANT:
            raise PermissionDenied("Only applicants can apply to job postings.")

        # If any non-draft app exists for this job/user, block ability to apply again
        already_submitted = Application.objects.filter(
            applicant=request.user,
            job=job
        ).exclude(status=Application.DR).exists()

        if already_submitted:
            existing = Application.objects.filter(applicant=request.user, job=job).exclude(status=Application.DR).first()
            return Response(
                {"detail": "You have already submitted an application for this job.", "application_id": existing.id},
                status=http_status.HTTP_409_CONFLICT
            )

        # Get existing or create new draft
        application, created = Application.objects.get_or_create(
            applicant=request.user,
            job=job,
            defaults={"status": Application.DR},
        )

        # Ensure answers exist for every question
        for q in job.questions.all():
            JobAppAnswer.objects.get_or_create(application=application, question=q)

        # Build response
        app_data = ApplicationSerializer(application, context={"request": request}).data

        answers = JobAppAnswer.objects.filter(application=application).select_related("question")
        answer_by_qid = {a.question_id: a for a in answers}

        questions_payload = []
        for q in job.questions.all():
            ans = answer_by_qid.get(q.id)
            questions_payload.append({
                "question": JobAppQuestionSerializer(q, context={"request": request}).data,
                "answer": JobAppAnswerSerializer(ans, context={"request": request}).data if ans else None,
            })

        return Response(
            {"application": app_data, "questions": questions_payload},
            status=http_status.HTTP_201_CREATED if created else http_status.HTTP_200_OK
        )


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.profile.account_type == Profile.ACCOUNT_EMPLOYER:
            # Employers can see all submitted applications for their company's job postings
            return Application.objects.filter(job__company=self.request.user.profile.company, status__in=["AP", "IN", "RE", "OF"])
        return Application.objects.filter(applicant=self.request.user)

    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        # Populate answers for all questions of the job on creation
        for q in application.job.questions.all():
            JobAppAnswer.objects.get_or_create(application=application, question=q)

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

        # Validate required questions have answers
        required_questions = application.job.questions.filter(required=True)
        missing_questions = []
        for q in required_questions:
            ans = application.answers.filter(question=q).first()
            if not ans or not ans.answer_value or not ans.answer_value.strip():
                missing_questions.append({"id": q.id, "prompt": q.question_prompt})

        if missing_questions:
            return Response({"detail": "Missing required questions.", "missing_questions": missing_questions}, status=http_status.HTTP_400_BAD_REQUEST)

        # Validate required application-level fields (resume required)
        if not application.resume:
            return Response({"detail": "Resume is required to submit an application."}, status=http_status.HTTP_400_BAD_REQUEST)

        # Transition status to Applied using transition method to validate allowed transitions
        try:
            application.transition_status(Application.AP)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST)

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

        try:
            application.transition_status(Application.DR) # try to mark as draft from applied
        except ValidationError as e: # catch any validation errors
            return Response({"detail": e.messages}, status=http_status.HTTP_400_BAD_REQUEST) # return error message and status code
        
        return Response({"id": application.id, "status": application.status}) # return updated application status
    
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
        if app.job.company != request.user.profile.company or request.user.profile.company is None:
            raise PermissionDenied("No permission.")
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
        
        if application.status != Application.DR:
            raise PermissionDenied("You can only answer questions for draft applications.")

        serializer.save()

    def perform_update(self, serializer):
        answer = self.get_object()
        if answer.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to update this answer.")
        if answer.application.status != Application.DR:
            raise PermissionDenied("You can only update answers for draft applications.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.application.applicant != self.request.user:
            raise PermissionDenied("You do not have permission to delete this answer.")
        if instance.application.status != Application.DR:
            raise PermissionDenied("You can only delete answers for draft applications.")
        instance.delete()