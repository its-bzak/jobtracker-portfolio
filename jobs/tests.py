from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Company, JobPosting, JobAppQuestion, JobAppAnswer, Application, Interview, Profile


class APIRoutes:
    REGISTER = "/api/auth/register/"
    LOGIN = "/api/auth/login/"
    REFRESH = "/api/auth/refresh/"
    # If you add logout later:
    # LOGOUT = "/api/auth/logout/"


class TestHelpers:
    @staticmethod
    def auth_headers(access_token: str) -> dict:
        return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}


class AuthFlowTests(APITestCase):
    def test_register_then_login_then_refresh(self):
        # Register
        payload = {"username": "testuser", "email": "test@example.com", "password": "4_Barczaks"}
        r = self.client.post(APIRoutes.REGISTER, payload, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        # Login
        r = self.client.post(APIRoutes.LOGIN, {"username": "testuser", "password": "4_Barczaks"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

        refresh = r.data["refresh"]

        # Refresh
        r = self.client.post(APIRoutes.REFRESH, {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)


class ApplicationFlowTests(APITestCase):
    def setUp(self):
        # Applicant user
        self.applicant = User.objects.create_user(username="applicant", password="pass12345", email="a@a.com")
        self.applicant.profile.account_type = Profile.ACCOUNT_APPLICANT
        self.applicant.profile.company = None
        self.applicant.profile.save()

        # Employer user + company
        self.company = Company.objects.create(name="TestCo")
        self.employer = User.objects.create_user(username="employer", password="pass12345", email="e@e.com")
        self.employer.profile.account_type = Profile.ACCOUNT_EMPLOYER
        self.employer.profile.company = self.company
        self.employer.profile.save()

        # Existing job + questions (we'll also test creating job via API)
        self.job = JobPosting.objects.create(
            title="Engineer",
            company=self.company,
            location="Remote",
            description="Desc",
        )

        self.q_required = JobAppQuestion.objects.create(
            job=self.job, question_prompt="Why do you want this job?", required=True
        )
        self.q_optional = JobAppQuestion.objects.create(
            job=self.job, question_prompt="Optional question", required=False
        )

    def login(self, username, password):
        r = self.client.post(APIRoutes.LOGIN, {"username": username, "password": password}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        return r.data["access"], r.data["refresh"]

    def test_employer_can_create_job_posting(self):
        self.client.force_authenticate(user=self.employer)

        payload = {
            "title": "Engineer",
            "location": "Remote",
            "description": "Great role",
            "employment_means": "RE",  # Remote (matches your model choices)
            "employment_type": "FT",   # Full-time (matches your model choices)
            "salary_range": "80k-100k",
        }

        r = self.client.post("/api/job-postings/", payload, format="json")
        print(r.status_code, r.data)  # helpful if it still fails
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        # sanity check: created job belongs to employer company
        self.assertEqual(r.data["company"], self.company.id)  # if serializer returns company


    def test_applicant_apply_creates_draft_and_answers(self):
        access, _ = self.login("applicant", "pass12345")

        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        self.assertIn("application", r.data)
        self.assertIn("questions", r.data)

        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)
        self.assertEqual(app.status, Application.DR)
        self.assertEqual(app.job, self.job)
        self.assertEqual(app.applicant, self.applicant)

        # answers exist for all job questions
        self.assertEqual(JobAppAnswer.objects.filter(application=app).count(), 2)

    def test_submit_requires_required_answers_and_resume(self):
        access, _ = self.login("applicant", "pass12345")

        # apply -> creates draft + answers
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)

        # submit with missing required answer -> 400 missing_questions
        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("missing_questions", r.data)

        # fill required answer
        ans = JobAppAnswer.objects.get(application=app, question=self.q_required)
        ans.answer_value = "Because I love it"
        ans.save()

        # submit without resume -> 400
        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

        # attach resume (PATCH app)
        resume = SimpleUploadedFile("resume.pdf", b"resume content", content_type="application/pdf")
        r = self.client.patch(
            f"/api/applications/{app.id}/",
            {"resume": resume},
            format="multipart",
            **TestHelpers.auth_headers(access),
        )
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED))

        # submit -> 200, status AP
        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Application.AP)

    def test_apply_after_submit_returns_409(self):
        access, _ = self.login("applicant", "pass12345")

        # create draft
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)

        # fill required answer + resume so we can submit
        JobAppAnswer.objects.filter(application=app, question=self.q_required).update(answer_value="ok")
        app.resume = SimpleUploadedFile("resume.pdf", b"x", content_type="application/pdf")
        app.save()

        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.AP)

        # apply again -> 409 conflict
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    def test_withdraw_reverts_to_draft(self):
        access, _ = self.login("applicant", "pass12345")

        # apply
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)

        # make it applied
        JobAppAnswer.objects.filter(application=app, question=self.q_required).update(answer_value="ok")
        app.resume = SimpleUploadedFile("resume.pdf", b"x", content_type="application/pdf")
        app.save()
        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # withdraw -> DR
        r = self.client.post(
            f"/api/applications/{app.id}/withdraw/",
            {},
            format="json",
            **TestHelpers.auth_headers(access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Application.DR)

    def test_employer_can_promote_offer_reject(self):
        # applicant applies + submits
        applicant_access, _ = self.login("applicant", "pass12345")
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(applicant_access),
        )
        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)
        JobAppAnswer.objects.filter(application=app, question=self.q_required).update(answer_value="ok")
        app.resume = SimpleUploadedFile("resume.pdf", b"x", content_type="application/pdf")
        app.save()
        r = self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(applicant_access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # employer promotes to interview
        employer_access, _ = self.login("employer", "pass12345")
        r = self.client.post(
            f"/api/applications/{app.id}/promote_to_interview/",
            {},
            format="json",
            **TestHelpers.auth_headers(employer_access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Application.IN)

        # employer offers
        r = self.client.post(
            f"/api/applications/{app.id}/offer/",
            {},
            format="json",
            **TestHelpers.auth_headers(employer_access),
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Application.OF)

    def test_interview_create_requires_application_in_interview_stage(self):
        # create applied app
        applicant_access, _ = self.login("applicant", "pass12345")
        r = self.client.post(
            f"/api/job-postings/{self.job.id}/apply/",
            {},
            format="json",
            **TestHelpers.auth_headers(applicant_access),
        )
        app_id = r.data["application"]["id"]
        app = Application.objects.get(id=app_id)
        JobAppAnswer.objects.filter(application=app, question=self.q_required).update(answer_value="ok")
        app.resume = SimpleUploadedFile("resume.pdf", b"x", content_type="application/pdf")
        app.save()
        self.client.post(
            f"/api/applications/{app.id}/submit/",
            {},
            format="json",
            **TestHelpers.auth_headers(applicant_access),
        )

        employer_access, _ = self.login("employer", "pass12345")

        # try to create interview while status is AP -> should fail
        payload = {
            "application": app.id,
            "interview_date": "2026-02-01T12:00:00Z",
            "interviewer_name": "Jane",
            "means_of_interview": "VI",
            "notes": "hello",
        }
        r = self.client.post(
            "/api/interviews/",
            payload,
            format="json",
            **TestHelpers.auth_headers(employer_access),
        )
        self.assertIn(r.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))

        # promote to interview then create
        self.client.post(
            f"/api/applications/{app.id}/promote_to_interview/",
            {},
            format="json",
            **TestHelpers.auth_headers(employer_access),
        )
        r = self.client.post(
            "/api/interviews/",
            payload,
            format="json",
            **TestHelpers.auth_headers(employer_access),
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Interview.objects.filter(application=app).exists())
