from django.contrib import admin
from .models import User, Project, Employee, Client, Logs, Contract, Section, Item, Task, ProjectPreset, UserPreset , Invoice
from django.http import HttpResponse
from openpyxl import Workbook
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

# Employee Admin
class EmployeeAdminForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = (
        'user', 
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
        'starting_date', 'holidays'
    )
    search_fields = ('user__username', 'user__email', 'salary')

    fieldsets = (
        (None, {'fields': ('user',)}),
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

# User Admin
admin.site.register(User, UserAdmin)

# Client Admin
# @admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_mail', 'firm_name', 'street_address', 'postal_code', 'city', 'country')
    search_fields = ('client_name', 'client_mail', 'firm_name', 'city', 'country')


# Export to Excel Function
def export_to_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="logs.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = 'Logs'
    
    # Define the columns, including separate Date and Time columns
    columns = ['Project Name', 'Contract', 'Section', 'Item', 'Task', 'Time Spent', 'Date', 'Time', 'User']
    ws.append(columns)
    
    for obj in queryset:
        # Split log_timestamps string into date and time
        log_timestamp = obj.log_timestamps
        if log_timestamp:
            try:
                log_date, log_time = log_timestamp.split(' ')
            except ValueError:
                log_date = log_time = ""
        else:
            log_date = log_time = ""

        row = [
            obj.log_project_name,
            obj.log_contract.contract_name if obj.log_contract else "",
            obj.log_section.section_name if obj.log_section else '',
            obj.log_Item.Item_name if obj.log_Item else "",
            obj.log_tasks if obj.log_tasks else "",
            str(obj.log_time),
            log_date,
            log_time,
            obj.user.username if obj.user else '',
        ]
        ws.append(row)
    
    wb.save(response)
    return response
export_to_excel.short_description = "Export Selected to Excel"

# Logs Admin
class LogsAdmin(admin.ModelAdmin):
    list_display = ['log_project_name', 'log_contract', 'log_section', 'log_Item', 'get_log_task', 'log_time', 'log_timestamps', 'user']
    actions = [export_to_excel]
    search_fields = ['log_project_name', 'log_contract__contract_name', 'log_section__section_name', 'log_Item__Item_name',  'user__username', 'log_timestamps']
    
    def get_log_task(self, obj):
        return obj.get_log_task()
    get_log_task.short_description = 'Tasks'

admin.site.register(Logs, LogsAdmin)

# Project Admin
class ProjectAdminForm(forms.ModelForm):
    contract = forms.ModelMultipleChoiceField(
        queryset=Contract.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Contracts", is_stacked=False)
    )
    
    class Meta:
        model = Project
        fields = '__all__'

class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('project_name', 'project_no', 'client_name', 'status', 'display_users')
    search_fields = ('project_name', 'project_no', 'client_name__name', 'status')

    def display_users(self, obj):
        return ", ".join([user.username for user in obj.user.all()])
    display_users.short_description = 'Users'

# admin.site.register(Project, ProjectAdmin)

# Item Admin
class ItemAdminForm(forms.ModelForm):
    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Tasks", is_stacked=False)
    )
    
    class Meta:
        model = Item
        fields = '__all__'

class ItemAdmin(admin.ModelAdmin):
    form = ItemAdminForm


# Section Admin
class SectionAdminForm(forms.ModelForm):
    Item = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Items", is_stacked=False)
    )
    
    class Meta:
        model = Section
        fields = '__all__'

class SectionAdmin(admin.ModelAdmin):
    form = SectionAdminForm
    list_display = ('section_name', 'section_billed_hourly')
    search_fields = ('section_name', 'section_billed_hourly')

admin.site.register(Section, SectionAdmin)

# Contract Admin
class ContractAdminForm(forms.ModelForm):
    section = forms.ModelMultipleChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Sections", is_stacked=False)
    )
    
    class Meta:
        model = Contract
        fields = '__all__'

class ContractAdmin(admin.ModelAdmin):
    form = ContractAdminForm

admin.site.register(Contract, ContractAdmin)


# Task Admin
# @admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_name', )
    search_fields = ('task_name',)  
    

# UserPreset Admin
class UserPresetAdminForm(forms.ModelForm):
    class Meta:
        model = UserPreset
        fields = '__all__'

    class Media:
        js = ('admin/js/projectpreset_admin.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user' in self.initial:
            user = self.initial['user']
        elif self.instance.pk:
            user = self.instance.user
        else:
            user = None
        if user:
            self.fields['project'].queryset = Project.objects.filter(user=user)

# @admin.register(UserPreset)
class UserPresetAdmin(admin.ModelAdmin):
    form = UserPresetAdminForm
    list_display = ('user', 'project', 'default_contract', 'default_section', 'default_Item', 'default_task')
    search_fields = ('user__username', 'project__project_name')

# ProjectPreset Admin
class ProjectPresetAdmin(admin.ModelAdmin):
    form = UserPresetAdminForm
    list_display = ('user', 'project', 'default_contract', 'default_section', 'default_Item', 'default_task')
    search_fields = ('user__username', 'project__project_name', 'default_contract__contract_name', 'default_section__section_name', 'default_Item__Item_name', 'default_task__task_name')

# admin.site.register(ProjectPreset, ProjectPresetAdmin)




from .models import SectionLibrary, ItemLibrary, TaskLibrary

class ItemLibraryInline(admin.TabularInline):
    model = ItemLibrary
    extra = 1

class TaskLibraryInline(admin.TabularInline):
    model = TaskLibrary
    extra = 1

@admin.register(SectionLibrary)
class SectionLibraryAdmin(admin.ModelAdmin):
    inlines = [ItemLibraryInline]

@admin.register(ItemLibrary)
class ItemLibraryAdmin(admin.ModelAdmin):
    inlines = [TaskLibraryInline]
    list_display = ('name', 'section')
    list_filter = ('section',)

@admin.register(TaskLibrary)
class TaskLibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'item')
    list_filter = ('item',)




admin.site.register(Item, ItemAdmin)



class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'contract', 'invoice_net', 'amount_received', 'created_at')
    search_fields = ('title', 'project__name', 'contract__name')
    list_filter = ('created_at',)

admin.site.register(Invoice, InvoiceAdmin)