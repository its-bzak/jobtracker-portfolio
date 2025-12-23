from django.contrib import admin
from .models import Profile, Company, JobPosting, Application, Interview, JobAppAnswer, JobAppQuestion
# Register your models here.

admin.site.register(JobPosting)
admin.site.register(Application)
admin.site.register(Interview)
#admin.site.register(Profile)
admin.site.register(Company)
@admin.register(JobAppAnswer)
class JobAppAnswerAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "question":
            app_id = request.GET.get("application")
            if app_id:
                try:
                    answer_app = Application.objects.get(pk=app_id)
                    kwargs["queryset"] = JobAppQuestion.objects.filter(job=answer_app.job)
                except Application.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
admin.site.register(JobAppQuestion)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): # Custom admin for Profile to ensure clean method is called
    def save_model(self, request, obj, form, change):
        obj.full_clean()  # This will call the clean() method on the model
        super().save_model(request, obj, form, change)