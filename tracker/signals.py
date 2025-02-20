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


from django.db.models.signals import post_delete
from .models import Contract, Invoice, InvoiceSettings, EstimateSettings

deleted_invoice_numbers = []  # Store deleted invoice numbers temporarily

from .models import DeletedInvoiceNumber

@receiver(post_delete, sender=Invoice)
def handle_invoice_deletion(sender, instance, **kwargs):
    """Handle invoice deletion to maintain sequence."""
    print(f"DEBUG: Invoice deleted - {instance.title}")

    try:
        invoice_number, _ = instance.title.split('-')  # Extract main invoice number
        invoice_number = int(invoice_number)

        # Retrieve the current invoice counter from settings
        settings = InvoiceSettings.objects.first()
        if settings:
            print(f"DEBUG: Current invoice counter before update: {settings.invoice_counter}")

            # If the deleted invoice number is not the most recent one, store it
            if invoice_number != settings.invoice_counter - 1:
                DeletedInvoiceNumber.objects.create(number=invoice_number)
                print(f"DEBUG: Stored deleted invoice number in DB: {invoice_number}")
            else:
                print(f"DEBUG: Invoice {invoice_number} was the most recent one, not storing.")

            # Check if the deleted number is the last in sequence and update counter
            if invoice_number == settings.invoice_counter - 1:
                settings.invoice_counter -= 1
                settings.save()
                print(f"DEBUG: Invoice counter updated to: {settings.invoice_counter}")

    except Exception as e:
        print(f"ERROR in handle_invoice_deletion: {e}")


@receiver(post_delete, sender=Contract)
def handle_contract_deletion(sender, instance, **kwargs):
    """Reset estimate consecutive number when a contract is deleted."""
    print(f"DEBUG: Contract deleted - {instance.contract_no}")

    try:
        # Extract only the first four digits as the contract number
        contract_number = instance.contract_no.split('-')[0]  # Take only the first segment
        contract_number = int(contract_number)  # Convert to integer

        settings = EstimateSettings.objects.first()
        if settings:
            print(f"DEBUG: Current estimate consecutive number before update: {settings.consecutive_start_no}")
            if contract_number == settings.consecutive_start_no - 1:
                settings.consecutive_start_no -= 1
                settings.save()
                print(f"DEBUG: Estimate consecutive number updated to: {settings.consecutive_start_no}")
    except Exception as e:
        print(f"ERROR in handle_contract_deletion: {e}")
