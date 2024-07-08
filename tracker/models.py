from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django_countries.fields import CountryField
from django.db.models import UniqueConstraint
from datetime import date

#Creating custom user model
class User(AbstractUser):
    pass


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
        return self.client_name


#Creating Task model
class Task(models.Model):
    task_name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.task_name


#Creating Item model
class Item(models.Model):
    Item_name = models.CharField(max_length=255, unique=True)
    tasks = models.ManyToManyField(Task)
    def __str__(self):
        return self.Item_name


#Creating Section model
class Section(models.Model):
    section_name = models.CharField(max_length=255, unique=True)
    user = models.ManyToManyField(User)
    allocated_budget = models.FloatField(default='0' )
    Item = models.ManyToManyField(Item)
    section_billed_hourly = models.BooleanField(default='False')
    def __str__(self):
        return self.section_name


#Creating Contract model
class Contract(models.Model):
    contract_name = models.CharField(max_length=255, unique=True)
    user = models.ManyToManyField(User)
    section = models.ManyToManyField(Section)
    def __str__(self):
        return self.contract_name


#Creating Project model
class Project(models.Model):
    status_choices = (('0', 'InProgress'), ('1', 'OnHold'), ('2', 'Completed'))
    project_name = models.CharField(max_length=100)
    project_address = models.CharField(max_length=100)
    client_name = models.ForeignKey('Client', on_delete=models.CASCADE)
    project_no = models.CharField(max_length=20)
    user = models.ManyToManyField(User)
    status = models.CharField(choices=status_choices, max_length=20)
    contract = models.ManyToManyField('Contract', blank=True)
    def __str__(self):
        return f"{self.project_no}-{self.project_name}"


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