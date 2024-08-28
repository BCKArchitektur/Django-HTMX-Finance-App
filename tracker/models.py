from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django_countries.fields import CountryField
from django.db.models import UniqueConstraint
from datetime import date
from django.utils import timezone
from decimal import Decimal

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
    def save(self, *args, **kwargs):
        self.total_salary = self.salary + (self.salary * (self.social_security_percentage / 100))
        super().save(*args, **kwargs)
    def __str__(self):
        return self.user.username


#Creating Client model
class Client(models.Model):
    client_name = models.CharField(max_length=255, unique=True,default='Unknown Name')
    client_mail = models.EmailField(max_length=255, unique=True, blank=True, null=True)  # Make email optional
    firm_name = models.CharField(max_length=255, unique=True, blank=True, null=True)  # Make firm name optional
    street_address = models.CharField(max_length=255,default='Unknown')
    postal_code = models.CharField(max_length=20,default='Unknown')
    city = models.CharField(max_length=100,default='Unknown')
    country = CountryField()  # Using django-countries for country field
    def __str__(self):
        return self.firm_name


#Creating Task model
class Task(models.Model):
    task_name = models.CharField(max_length=255, unique=False)
    def __str__(self):
        return self.task_name


class Item(models.Model):
    UNIT_CHOICES = [
        ('Std', 'Std'),
        ('Psch', 'Psch'),
        ('Stk', 'Stk'),
    ]

    Item_name = models.CharField(max_length=255, unique=False)
    description = models.TextField(blank=True, null=True)
    tasks = models.ManyToManyField(Task)
    users = models.ManyToManyField(User, blank=True)
    quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='Std')
    rate = models.FloatField(default=0.0)
    total = models.FloatField(default=0.0, editable=False)

    def __str__(self):
        return self.Item_name

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.rate
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for task in self.tasks.all():
            task.delete()
        super().delete(*args, **kwargs)





#Creating Section model
class Section(models.Model):
    section_name = models.CharField(max_length=255, unique=False)
    user = models.ManyToManyField(User)
    allocated_budget = models.FloatField(default='0')
    Item = models.ManyToManyField(Item)
    section_billed_hourly = models.BooleanField(default='False')

    def __str__(self):
        return self.section_name
    
    def delete(self, *args, **kwargs):
        for item in self.Item.all():
            item.delete()  # Delete all items related to this section
        super().delete(*args, **kwargs)




#Creating Contract model
class Contract(models.Model):
    contract_name = models.CharField(max_length=255, unique=False)
    user = models.ManyToManyField(User)
    section = models.ManyToManyField(Section)
    additional_fee_percentage = models.FloatField(default=6.5) 
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=19.00,blank=True, null=True) 

    def __str__(self):
        return self.contract_name

    def delete(self, *args, **kwargs):
        for section in self.section.all():
            section.delete()  # Delete all sections related to this contract
        super().delete(*args, **kwargs)





#Creating Project model
class Project(models.Model):
    status_choices = (('0', 'InProgress'), ('1', 'OnHold'), ('2', 'Completed'))
    project_name = models.CharField(max_length=100)
    project_address = models.CharField(max_length=100 )
    client_name = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)
    project_no = models.CharField(max_length=20)
    user = models.ManyToManyField(User)
    status = models.CharField(choices=status_choices, max_length=20)
    contract = models.ManyToManyField('Contract', blank=True)

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
    

class SectionLibrary(models.Model):
    name = models.CharField(max_length=255)
    section_billed_hourly = models.BooleanField(default='False')

    def __str__(self):
        return self.name

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
    

class Invoice(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('SR', 'Schlussrechnung'),  # Final invoice
        ('AR', 'Abschlagsrechnung'),  # Partial invoice
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    provided_quantities = models.JSONField(default=dict)
    invoice_net = models.FloatField()
    invoice_gross = models.FloatField(editable=False)  # New field for Invoice Gross
    amount_received = models.FloatField(null=True, blank=True, default=0)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    invoice_type = models.CharField(max_length=2, choices=INVOICE_TYPE_CHOICES, default='AR')  # New field for invoice type

    def save(self, *args, **kwargs):
        # Retrieve the VAT percentage from the associated contract
        vat_percentage = Decimal(self.contract.vat_percentage) 
        
        # Calculate the invoice gross based on invoice net and VAT percentage
        self.invoice_gross = float(Decimal(self.invoice_net) * (1 + vat_percentage / Decimal(100)))

        if not self.title:
            year = timezone.now().year % 100  # Get last two digits of the year
            month = timezone.now().month

            # Create the filter format based on year and month
            prefix = f"{year:02d}"  # Ensures year is always two digits

            # Count how many invoices have this prefix in their title
            count = Invoice.objects.count() + 700
            
            # Determine the invoice type prefix ('AR' or 'SR')
            type_prefix = self.invoice_type
            
            # Generate the title using the format yycount-month with the type prefix
            self.title = f"{type_prefix}-{prefix}{count}-{month:02d}"  # Ensures month is always two digits
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
