from .models import Profile
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, **kwargs):
    Profile.objects.get_or_create(
        user=instance,
        defaults={"account_type": Profile.ACCOUNT_APPLICANT},
    )