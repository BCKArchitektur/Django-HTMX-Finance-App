from django.contrib import admin
from .models import User, Project, Employee, Client, Logs, Contract, Section, Item, Task, ProjectPreset , UserPreset
from django.http import HttpResponse
from openpyxl import Workbook
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

class EmployeeAdminForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'


class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = (
        'user', 
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
        # 'salary', 'social_security_percentage', 'total_salary', 
        'starting_date', 'holidays'
    )
    search_fields = ('user__username', 'user__email', 'salary')

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Work Schedule', {
            'fields': (
                'hours_assigned_monday', 'hours_assigned_tuesday', 'hours_assigned_wednesday', 'hours_assigned_thursday', 'hours_assigned_friday'
            ),
            'classes': ('wide', 'work-schedule-grid')
        }),
        ('Additional Information', {
            'fields': ('salary', 'social_security_percentage', 'total_salary', 'starting_date', 'holidays'),
            'classes': ('wide',)
        }),
    )

    readonly_fields = ('total_salary',)

    def monday(self, obj):
        return obj.hours_assigned_monday
    monday.short_description = 'Monday'

    def tuesday(self, obj):
        return obj.hours_assigned_tuesday
    tuesday.short_description = 'Tuesday'

    def wednesday(self, obj):
        return obj.hours_assigned_wednesday
    wednesday.short_description = 'Wednesday'

    def thursday(self, obj):
        return obj.hours_assigned_thursday
    thursday.short_description = 'Thursday'

    def friday(self, obj):
        return obj.hours_assigned_friday
    friday.short_description = 'Friday'

    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }

admin.site.register(Employee, EmployeeAdmin)

admin.site.register(User, UserAdmin)
