from django.contrib import admin
from .models import JobPosting, Application, Interview
# Register your models here.

admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Interview)