from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Contract, EstimateInvoiceSettings

@receiver(post_save, sender=Contract)
def increment_consecutive_start_no(sender, instance, created, **kwargs):
    if created:  # Only when a new contract is created
        settings = EstimateInvoiceSettings.objects.first()
        if settings:
            settings.consecutive_start_no += 1
            settings.save()
