from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Contract, EstimateSettings, InvoiceSettings

@receiver(post_save, sender=Contract)
def increment_consecutive_start_no(sender, instance, created, **kwargs):
    """Increment estimate consecutive number when a new contract is created."""
    if created:  # Only when a new contract is created
        settings = EstimateSettings.objects.first()
        if settings:
            settings.consecutive_start_no += 1
            settings.save()

@receiver(post_save, sender=Contract)
def increment_invoice_counter(sender, instance, created, **kwargs):
    """Increment invoice counter when a new contract is created."""
    if created:  # Only when a new contract is created
        settings = InvoiceSettings.objects.first()
        if settings:
            settings.invoice_counter += 1
            settings.save()
