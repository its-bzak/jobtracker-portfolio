from django.contrib import admin
from .models import Profile, Company, JobPosting, Application, Interview, JobAppAnswer, JobAppQuestion
# Register your models here.

admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Interview)
#admin.site.register(Profile)
admin.site.register(Company)
admin.site.register(JobAppAnswer)
admin.site.register(JobAppQuestion)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): # Custom admin for Profile to ensure clean method is called
    def save_model(self, request, obj, form, change):
        obj.full_clean()  # This will call the clean() method on the model
        super().save_model(request, obj, form, change)