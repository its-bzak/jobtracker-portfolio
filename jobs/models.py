from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.

class Profile(models.Model):
    ACCOUNT_APPLICANT = 'AP'
    ACCOUNT_EMPLOYER = 'EM'


    ACCOUNT_TYPES = [
        (ACCOUNT_APPLICANT, 'Applicant'),
        (ACCOUNT_EMPLOYER, 'Employer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    account_type = models.CharField(max_length=2, choices=ACCOUNT_TYPES, default=ACCOUNT_APPLICANT)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    company = models.ForeignKey('Company', on_delete=models.SET_NULL, blank=True, null=True)

    def clean(self):
        super().clean()
        if self.account_type == self.ACCOUNT_APPLICANT and self.company is not None:
            raise ValidationError({ # Raise validation error if an applicant profile is linked to a company
                "company": "Applicants cannot be associated with a company."
            })
        # If the profile is an employer, a company association is not mandatory, so no need to validate that case.


    def __str__(self):
        return f"{self.user.username} - {self.account_type}"
    
class Company(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class JobPosting(models.Model):
    title = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE) # Each job posting is linked to a company
    location = models.CharField(max_length=100)
    employment_means = models.CharField(max_length=2, choices=[
        ('RE', 'Remote'),
        ('ON', 'On-site'),
        ('HY', 'Hybrid'),
    ], default='ON')
    salary_range = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(max_length=1000)
    posted_date = models.DateField(auto_now_add=True)

    employment_type = models.CharField(max_length=2, choices=[
        ('FT', 'Full-time'),
        ('PT', 'Part-time'),
        ('CT', 'Contract'),
        ('IN', 'Internship'),
    ], default='FT')

    def __str__(self):
        return f"{self.title} at {self.company.name}"

class Application(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE) # Each application is linked to a profile
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE) # Each application is linked to a job posting
    application_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=[
        ('DR', 'Draft'),
        ('AP', 'Applied'),
        ('IN', 'Interview'),
        ('OF', 'Offer'),
        ('RE', 'Rejection'),
    ], default='DR')

    DR = 'DR' ; AP = 'AP' ; IN = 'IN' ; OF = 'OF' ; RE = 'RE'
    ACCEPTED_STATUSES = {
        DR: {AP},
        AP: {DR, IN, OF, RE},
        IN: {OF, RE},
        OF: set(),
        RE: set(),
    }

    def transition_status(self, new_status):
        if new_status not in self.ACCEPTED_STATUSES[self.status]:
            raise ValidationError(f"Cannot transition from status {self.status} to status {new_status}.")
        self.status = new_status
        self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.job.title} at {self.job.company.name} - {self.applicant.username}"
    
    class Meta:
        unique_together = ('applicant', 'job')  # Prevent duplicate applications for the same job by the same user

class Interview(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE) # Each interview is linked to an application
    interview_date = models.DateTimeField()
    interviewer_name = models.CharField(max_length=100)
    notes = models.TextField(max_length=1000, blank=True, null=True)
    means_of_interview = models.CharField(max_length=2, choices=[
        ('PH', 'Phone'),
        ('VI', 'Video Call'),
        ('IN', 'In-Person'),
    ], default='PH')

    def __str__(self):
        return f"Interview for {self.application.job.title} with {self.interviewer_name} on {self.interview_date}"