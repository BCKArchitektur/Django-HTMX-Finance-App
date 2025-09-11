from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django_countries.fields import CountryField
from django.db.models import UniqueConstraint
from datetime import date
from django.utils import timezone
from decimal import Decimal
import os
from django.db.models import JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError

#Creating custom user model
class User(AbstractUser):
    dark_mode = models.BooleanField(default=False)

#Creating Employee model
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hours_assigned_monday = models.IntegerField(default=0)
    hours_assigned_tuesday = models.IntegerField(default=0)
    hours_assigned_wednesday = models.IntegerField(default=0)
    hours_assigned_thursday = models.IntegerField(default=0)
    hours_assigned_friday = models.IntegerField(default=0)
    salary = models.FloatField(default=0.0)
    social_security_percentage = models.FloatField(default=0.0)
    total_salary = models.FloatField(editable=False, default=0.0)
    starting_date = models.DateField(null=True, blank=True)
    holidays = models.IntegerField(default=0)
    date_override = models.BooleanField(default=False, help_text="Allow unrestricted date selection in log entries.")

    def save(self, *args, **kwargs):
        # Ensure total_salary is recalculated
        self.total_salary = self.salary + (self.salary * (self.social_security_percentage / 100))
        # Ensure date_override is True if user.is_staff is True
        if self.user.is_staff:
            self.date_override = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

# Creating Client model
class Client(models.Model):
    client_name = models.CharField(max_length=255, unique=False, default='Unknown Name')
    client_mail = models.EmailField(max_length=255, unique=False, blank=True, null=True)  
    client_phone = models.CharField(blank=True, null=True) 
    firm_name = models.CharField(max_length=255, unique=True, blank=True, null=True)  
    street_address = models.CharField(max_length=255, default='Unknown')
    postal_code = models.CharField(max_length=20, default='Unknown')
    city = models.CharField(max_length=100, default='Unknown')
    country = CountryField()  # django-countries for country field

    def __str__(self):
        return self.firm_name or self.client_name

#Creating Task model
class Task(models.Model):
    task_name = models.CharField(max_length=255, unique=False)
    def __str__(self):
        return self.task_name

#Creating Item model
class Item(models.Model):
    UNIT_CHOICES = [
        ('Std', 'Std'),
        ('Psch', 'Psch'),
        ('Stk', 'Stk'),
        ('%', '%'),
        ('Monat(e)', 'Monat(e)'),
        ('Tag(e)', 'Tag(e)'),
    ]

    Item_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tasks = models.ManyToManyField('Task')
    users = models.ManyToManyField(User, blank=True)
    quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='Std')
    rate = models.FloatField(default=0.0)
    total = models.FloatField(default=0.0, editable=False)
    order = models.IntegerField(default=0)

    # Transient project holder (not a field)
    _project = None

    HOURLY_RATES_MAPPING = {
        "Geschäftsführung": "executive_management_rate",
        "Architekt/in": "architect_rate",
        "Bautechniker/in": "construction_technician_rate",
        "Projektleitung": "project_management_rate",
        "Fachplaner/in": "specialist_planner_rate",
        "Bauüberwachung": "construction_supervision_rate",
        "Computational Architect": "computational_architect_rate",
        "Bauzeichner/in": "draftsman_rate",
    }

    def set_project_context(self, project):
        """Temporarily attach a project to the Item instance before saving."""
        self._project = project


    def get_applicable_rate(self):
        print(f"\nEvaluating rate for item: '{self.Item_name}'")
        
        rate_field = self.HOURLY_RATES_MAPPING.get(self.Item_name)
        if not rate_field:
            print("No matching rate field in HOURLY_RATES_MAPPING.")
            return self.rate

        print(f"Mapped to rate field: '{rate_field}'")

        # 1. Check for project override
        if self._project:
            print("Project context is set.")
            print("hourly_rates_override:", self._project.hourly_rates_override)

            override_data = getattr(self._project, "hourly_rates_override", None)
            if isinstance(override_data, dict):
                override_rate = override_data.get(rate_field)
                if override_rate is not None:
                    print(f"Found override rate: {override_rate}")
                    return float(override_rate)
                else:
                    print("No override rate found for this field.")
            else:
                print("hourly_rates_override is None or not a dictionary.")

        else:
            print("No project context provided.")

        # 2. Fallback to EstimateSettings default
        try:
            estimate_settings = EstimateSettings.objects.first()
            if estimate_settings:
                default_rate = getattr(estimate_settings, rate_field, None)
                if default_rate is not None:
                    print(f"Using default rate from EstimateSettings: {default_rate}")
                    return float(default_rate)
                else:
                    print(f"EstimateSettings does not define a value for '{rate_field}'")
            else:
                print("No EstimateSettings instance found.")
        except ObjectDoesNotExist:
            print("Failed to retrieve EstimateSettings.")

        print("Returning existing item.rate:", self.rate)
        return self.rate


    def save(self, *args, **kwargs):
        print(f"\nSaving item: '{self.Item_name}' with quantity: {self.quantity}")
        self.rate = self.get_applicable_rate()
        self.total = float(self.quantity) * float(self.rate)
        print(f"Final rate set to: {self.rate}")
        print(f"Total calculated: {self.total}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.Item_name




#Creating Section model
class Section(models.Model):
    section_name = models.CharField(max_length=255, unique=False)
    user = models.ManyToManyField(User)
    allocated_budget = models.FloatField(default='0')
    Item = models.ManyToManyField(Item)
    section_billed_hourly = models.BooleanField(default='False')
    order = models.IntegerField(default=0) 
    exclude_from_nachlass = models.BooleanField(default=False)

    def __str__(self):
        return self.section_name
    
    def delete(self, *args, **kwargs):
        for item in self.Item.all():
            item.delete()  # Delete all items related to this section
        super().delete(*args, **kwargs)


#Creating Contract model
from django_quill.fields import QuillField

class Contract(models.Model):
    contract_name = models.CharField(max_length=255, unique=False)
    user = models.ManyToManyField(User)
    section = models.ManyToManyField(Section)
    additional_fee_percentage = models.FloatField(default=6.5,blank=True, null=True)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, blank=True, null=True)
    contract_no = models.CharField(max_length=255, unique=True, blank=True, null=True)  # Concatenated field
    scope_of_work = models.TextField(blank=True, null=True)
    hoai_data = models.JSONField(default=dict, blank=True, null=True)  # Store HOAI inputs
    zuschlag_value = models.CharField(max_length=255,default=0, blank=True, null=True)  # New Field
    nachlass_value = models.CharField(max_length=255,default=0, blank=True, null=True)
    nachlass_percentage = models.CharField(max_length=255,default=0, blank=True, null=True)

    def __str__(self):
        return f"({self.contract_no}-{self.contract_name} )"

    def delete(self, *args, **kwargs):
        for section in self.section.all():
            section.delete()  # Delete all sections related to this contract
        super().delete(*args, **kwargs)


#Creating Project model
class Project(models.Model):
    
    status_choices =  (('0', 'InBearbeitung'),
        ('1', 'Zurückgestellt'),
        ('2', 'Abgeschlossen '),
        ('3', 'Eingestellt'),)
    project_name = models.CharField(max_length=100)
    project_address = models.CharField(max_length=100 )
    client_name = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)
    project_no = models.CharField(max_length=20)
    user = models.ManyToManyField(User)
    status = models.CharField(choices=status_choices, max_length=20)
    contract = models.ManyToManyField('Contract', blank=True)
    hourly_rates_override = JSONField(null=True, blank=True, help_text="Custom hourly rates for this project")

    def __str__(self):
        return f"{self.project_no}-{self.project_name}"

    def delete(self, *args, **kwargs):
        for contract in self.contract.all():
            contract.delete()  # Delete all contracts related to this project
        super().delete(*args, **kwargs)


#Creating Logs model
class Logs(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='logs', null=True)
    log_project_name = models.CharField(max_length=100)
    log_contract = models.ForeignKey('Contract', on_delete=models.CASCADE)
    log_section = models.ForeignKey('Section', on_delete=models.CASCADE)
    log_Item = models.ForeignKey('Item', on_delete=models.CASCADE)
    log_tasks = models.CharField(max_length=255, blank=True, null=True)  # Updated field for tasks
    log_time = models.FloatField()
    log_timestamps = models.CharField(max_length=100)
    def get_log_task(self):
        return self.log_tasks
    def __str__(self):
        return f"{self.log_timestamps}-{self.log_project_name}-{self.log_contract}-{self.get_log_task()}-{self.log_section}-{self.log_time}-{self.user}"
     
#Creating Preset model
class ProjectPreset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='1')
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    default_contract = models.ForeignKey('Contract', on_delete=models.SET_NULL, null=True, blank=True)
    default_section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True)
    default_Item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, blank=True)
    default_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"Preset for {self.user.username} - {self.project.project_name}"

#Creating UserPreset model
class UserPreset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='1')
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    default_contract = models.ForeignKey('Contract', on_delete=models.SET_NULL, null=True, blank=True)
    default_section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True)
    default_Item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, blank=True)
    default_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return f"Preset for {self.user.username} - {self.project.project_name}"
    
#Creating sectionlibrary model
class SectionLibrary(models.Model):
    name = models.CharField(max_length=255)
    section_billed_hourly = models.BooleanField(default='False')

    def __str__(self):
        return self.name

#Creating itemlibrary model
class ItemLibrary(models.Model):
    section = models.ForeignKey(SectionLibrary, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class TaskLibrary(models.Model):
    item = models.ForeignKey(ItemLibrary, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class DeletedInvoiceNumber(models.Model):
    number = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.number)


class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('ER', 'Einzelrechnung (Individual Invoice)'),  # Standard invoice
        ('AR', 'Abschlagsrechnung (Partial/Progress Invoice)'),  # Partial invoice
        ('SR', 'Schlussrechnung (Final Invoice)'),  # Final invoice
        ('ZR', 'Anzahlungsrechnung (Advance Payment Invoice)'),  # Advance payment invoice
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    provided_quantities = models.JSONField(default=dict)
    invoice_net = models.FloatField()
    current_invoice_net = models.FloatField(default=0.0)  # Used for cumulative invoices
    invoice_gross = models.FloatField(editable=False)  # Automatically calculated
    amount_received = models.FloatField(null=True, blank=True, default=0)
    title = models.CharField(max_length=200, unique=True)  # Ensure uniqueness
    created_at = models.DateTimeField(default=timezone.now)
    invoice_type = models.CharField(max_length=2, choices=INVOICE_TYPE_CHOICES, default='ER')  # Default to Individual Invoice
    is_cumulative = models.BooleanField(null=True, blank=True, default=None)
    date_of_payment = models.DateField(null=True, blank=True) 
    current_ar_number = models.IntegerField(null=True, blank=True, default=0)  # New field for tracking AR numbers
    
    def save(self, *args, **kwargs):
            # Always keep gross in sync
            vat_percentage = Decimal(self.contract.vat_percentage)
            self.invoice_gross = float(Decimal(self.invoice_net) * (1 + vat_percentage / Decimal(100)))

            # If title already set manually, just save normally
            if self.title:
                return super().save(*args, **kwargs)

            month = timezone.now().month

            # Try numbers until one succeeds; serialize access to the counter
            with transaction.atomic():
                settings, _ = InvoiceSettings.objects.select_for_update().get_or_create(id=1)

                # We’ll try: (a) recycled numbers first, then (b) monotonically increasing counter
                tried_numbers = set()

                while True:
                    # 1) Prefer reusing the smallest deleted number
                    deleted = DeletedInvoiceNumber.objects.order_by('number').first()
                    if deleted:
                        candidate = deleted.number
                        # Remove so it won't be picked by another concurrent txn
                        deleted.delete()
                    else:
                        # 2) Otherwise use the counter or the next after what we've tried
                        candidate = max(settings.invoice_counter, (max(tried_numbers) + 1) if tried_numbers else settings.invoice_counter)

                    self.title = f"{candidate}-{month:02d}"

                    try:
                        super().save(*args, **kwargs)
                    except IntegrityError:
                        # Title collision (unique constraint) → try next number
                        tried_numbers.add(candidate)
                        continue
                    else:
                        # Success → advance counter if we consumed the current/greater number
                        if candidate >= settings.invoice_counter:
                            settings.invoice_counter = candidate + 1
                            settings.save(update_fields=['invoice_counter'])
                        break  # done

    @property
    def current_invoice_gross(self):
        """Gross value of the current invoice (based on current_invoice_net)."""
        vat_percentage = Decimal(self.contract.vat_percentage)
        return float(Decimal(self.current_invoice_net) * (1 + vat_percentage / Decimal(100)))

    def __str__(self):
        return self.title
    
    def formatted_created_at(self):
        """Return the created_at datetime in German format: DD.MM.YYYY HH:MM."""
        if self.created_at:
            return self.created_at.strftime("%d.%m.%Y %H:%M")
        return None
    
    def formatted_date_of_payment(self):
        """Return the date_of_payment in German format: DD.MM.YYYY."""
        if self.date_of_payment:
            return self.date_of_payment.strftime("%d.%m.%Y")
        return None


from django.db import models
import os

class EstimateSettings(models.Model):
    """Stores settings related to estimates and hourly rates."""
    
    consecutive_start_no = models.IntegerField(default=1, help_text="Starting number for consecutive numbering.")

    # Estimate Templates
    bck_eng_template = models.FileField(upload_to='templates/estimates/', null=True, blank=True)
    bck_de_template = models.FileField(upload_to='templates/estimates/', null=True, blank=True)
    kost_eng_template = models.FileField(upload_to='templates/estimates/', null=True, blank=True)
    kost_de_template = models.FileField(upload_to='templates/estimates/', null=True, blank=True)

    # Hourly Rates
    executive_management_rate = models.DecimalField(max_digits=10, decimal_places=2, default=250, help_text="Rate for Geschäftsführung (Executive Management)")
    specialist_planner_rate = models.DecimalField(max_digits=10, decimal_places=2, default=185, help_text="Rate for Fachplaner/In (Specialist Planner)")
    project_management_rate = models.DecimalField(max_digits=10, decimal_places=2, default=165, help_text="Rate for Projektleitung (Project Management)")
    construction_supervision_rate = models.DecimalField(max_digits=10, decimal_places=2, default=155, help_text="Rate for Bauüberwachung (Construction Supervision)")
    computational_architect_rate = models.DecimalField(max_digits=10, decimal_places=2, default=155, help_text="Rate for Computational Architect")
    architect_rate = models.DecimalField(max_digits=10, decimal_places=2, default=145, help_text="Rate for Architekt/In (Architect)")
    construction_technician_rate = models.DecimalField(max_digits=10, decimal_places=2, default=135, help_text="Rate for Bautechniker/In (Construction Technician)")
    draftsman_rate = models.DecimalField(max_digits=10, decimal_places=2, default=115, help_text="Rate for Zeichner (Draftsman)")

    def save(self, *args, **kwargs):
        """Ensures old files are removed when a new file is uploaded."""
        if self.pk:
            old_instance = EstimateSettings.objects.get(pk=self.pk)
            fields_to_check = [
                'bck_eng_template',
                'bck_de_template',
                'kost_eng_template',
                'kost_de_template',
            ]

            for field in fields_to_check:
                old_file = getattr(old_instance, field)
                new_file = getattr(self, field)

                if old_file and old_file != new_file:
                    if os.path.isfile(old_file.path):
                        os.remove(old_file.path)

        super().save(*args, **kwargs)

    def __str__(self):
        return "Estimate Settings"



class InvoiceSettings(models.Model):
    """Stores settings related to invoices."""
    invoice_counter = models.IntegerField(default=1, help_text="Counter for generating invoice numbers.")

    # Invoice Templates
    inv_bck_eng_template = models.FileField(upload_to='templates/invoices/', null=True, blank=True)
    inv_bck_de_template = models.FileField(upload_to='templates/invoices/', null=True, blank=True)
    inv_kost_eng_template = models.FileField(upload_to='templates/invoices/', null=True, blank=True)
    inv_kost_de_template = models.FileField(upload_to='templates/invoices/', null=True, blank=True)

    def save(self, *args, **kwargs):
        """Ensures old files are removed when a new file is uploaded."""
        if self.pk:
            old_instance = InvoiceSettings.objects.get(pk=self.pk)
            fields_to_check = [
                'inv_bck_eng_template',
                'inv_bck_de_template',
                'inv_kost_eng_template',
                'inv_kost_de_template',
            ]

            for field in fields_to_check:
                old_file = getattr(old_instance, field)
                new_file = getattr(self, field)

                if old_file and old_file != new_file:
                    if os.path.isfile(old_file.path):
                        os.remove(old_file.path)

        super().save(*args, **kwargs)

    def __str__(self):
        return "Invoice Settings"

def default_lp_breakdown():
    """Returns a default LP breakdown dictionary."""
    return {
        "lp1": 2,
        "lp2": 7,
        "lp3": 15,
        "lp4": 3,
        "lp5": 25,
        "lp6": 10,
        "lp7": 4,
        "lp8": 32,
        "lp9": 2
    }

class ServiceProfile(models.Model):
    """Stores different HOAI service profiles, their Excel files, and LP breakdowns."""
    name = models.CharField(max_length=255, unique=True)  # Profile Name (e.g., "HOAI 2021 - Buildings")
    excel_file = models.FileField(upload_to='hoai_tables/')  # File upload location
    no_of_Honarzone = models.IntegerField(default=5)
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp for file upload

    # New field: Store LP percentages as JSON
    lp_breakdown = models.JSONField(default=default_lp_breakdown) 

    def __str__(self):
        return self.name