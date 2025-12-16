from django.contrib import admin
from .models import Profile, Company, JobPosting, Application, Interview
# Register your models here.

admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Interview)
admin.site.register(Profile)
admin.site.register(Company)