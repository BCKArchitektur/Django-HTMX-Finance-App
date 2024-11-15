from django import forms
from .models import Project, Contract, Section, Item, Logs , Task , Client , User , Invoice



class LogForm(forms.ModelForm):
    log_project_name = forms.ModelChoiceField(queryset=Project.objects.none(), label="Project")
    log_contract = forms.ModelChoiceField(queryset=Contract.objects.none(), required=True, label="Contract")
    log_section = forms.ModelChoiceField(queryset=Section.objects.none(), required=True, label="Section")
    log_Item = forms.ModelChoiceField(queryset=Item.objects.none(), required=True, label="Item")
    log_tasks = forms.CharField(widget=forms.HiddenInput(), label="Tasks", required=True)

    TIME_CHOICES = (
        ('', 'Select Time'),
        ('0.25', '15min'),
        ('0.50', '30min'),
        ('0.75', '45min'),
        ('1.00', '1hr'),
        ('1.25', '1hr 15min'),
        ('1.50', '1hr 30min'),
        ('1.75', '1hr 45min'),
        ('2.00', '2hr'),
        ('2.25', '2hr 15min'),
        ('2.50', '2hr 30min'),
        ('2.75', '2hr 45min'),
        ('3.00', '3hr'),
        ('3.25', '3hr 15min'),
        ('3.50', '3hr 30min'),
        ('3.75', '3hr 45min'),
        ('4.00', '4hr'),
        ('4.25', '4hr 15min'),
        ('4.50', '4hr 30min'),
        ('4.75', '4hr 45min'),
        ('5.00', '5hr'),
        ('5.25', '5hr 15min'),
        ('5.50', '5hr 30min'),
        ('5.75', '5hr 45min'),
        ('6.00', '6hr'),
        ('6.25', '6hr 15min'),
        ('6.50', '6hr 30min'),
        ('6.75', '6hr 45min'),
        ('7.00', '7hr'),
        ('7.25', '7hr 15min'),
        ('7.50', '7hr 30min'),
        ('7.75', '7hr 45min'),
        ('8.00', '8hr'),
    )
    log_time = forms.ChoiceField(choices=TIME_CHOICES, label="Time", initial='', required=True)
     
    log_date = forms.CharField(widget=forms.HiddenInput(), required=False)  # CharField for date

    class Meta:
        model = Logs
        fields = ['log_project_name', 'log_contract', 'log_section', 'log_Item', 'log_tasks', 'log_time']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LogForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['log_project_name'].queryset = Project.objects.filter(user=user)
            if self.is_bound:
                project_id = self.data.get('log_project_name')
                contract_id = self.data.get('log_contract')
                section_id = self.data.get('log_section')

                if project_id:
                    self.fields['log_contract'].queryset = Contract.objects.filter(project__id=project_id, user=user)
                if contract_id:
                    self.fields['log_section'].queryset = Section.objects.filter(contract__id=contract_id, user=user)
                if section_id:
                    self.fields['log_Item'].queryset = Item.objects.filter(section__id=section_id, users=user)
            else:
                self.fields['log_contract'].queryset = Contract.objects.none()
                self.fields['log_section'].queryset = Section.objects.none()
                self.fields['log_Item'].queryset = Item.objects.none()



class Hiddenform(forms.Form):
    log_project_name = forms.CharField(max_length=50)
    log_contract = forms.CharField(max_length=50)
    log_section = forms.CharField(max_length=50)
    log_Item = forms.CharField(max_length=50)
    log_tasks = forms.CharField(max_length=255)  # Updated to handle multiple tasks as a comma-separated string
    log_time = forms.CharField(max_length=50)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(Hiddenform, self).__init__(*args, **kwargs)

class ProjectPresetForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), label="Project")
    default_contract = forms.ModelChoiceField(queryset=Contract.objects.none(), required=True, label="Default Contract")
    default_section = forms.ModelChoiceField(queryset=Section.objects.none(), required=True, label="Default Section")
    default_Item = forms.ModelChoiceField(queryset=Item.objects.none(), required=True, label="Default Item")
    default_task = forms.ModelChoiceField(queryset=Task.objects.none(), required=False, label="Default Task")
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProjectPresetForm, self).__init__(*args, **kwargs)
        if self.is_bound:
            self.fields['default_contract'].queryset = Contract.objects.filter(project=self.data.get('project'))
            self.fields['default_section'].queryset = Section.objects.filter(contract=self.data.get('default_contract'))
            self.fields['default_Item'].queryset = Item.objects.filter(section=self.data.get('default_section'))
            self.fields['default_task'].queryset = Task.objects.filter(Item=self.data.get('default_Item'))
        else:
            self.fields['default_contract'].queryset = Contract.objects.none()
            self.fields['default_section'].queryset = Section.objects.none()
            self.fields['default_Item'].queryset = Item.objects.none()
            self.fields['default_task'].queryset = Task.objects.none()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'project_address', 'client_name', 'project_no', 'status', 'user']



class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['client_name', 'client_mail', 'firm_name', 'street_address', 'postal_code', 'city', 'country']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'Client Name'}),
            'client_mail': forms.EmailInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'Client Email'}),
            'firm_name': forms.TextInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'Firm Name'}),
            'street_address': forms.TextInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'Street Address'}),
            'postal_code': forms.TextInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'Postal Code'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full max-w-xs m-2', 'placeholder': 'City'}),
            'country': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs m-2'}),
        }

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['contract_name', 'vat_percentage']  # Include vat_percentage

class AddUsersForm(forms.Form):
    items = forms.ModelChoiceField(queryset=Item.objects.all(), label="Select Item")
    users = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.CheckboxSelectMultiple, label="Select Users")

class AddBudgetForm(forms.Form):
    items = forms.ModelChoiceField(queryset=Item.objects.all(), label="Select Item")
    quantity = forms.FloatField(label="Quantity")
    unit = forms.ChoiceField(choices=Item.UNIT_CHOICES, label="Unit")
    rate = forms.FloatField(label="Rate")
    total = forms.FloatField(label="Total", required=False)  # This field will be automatically calculated

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['contract', 'provided_quantities', 'invoice_net', 'amount_received', 'invoice_type']  # Added 'invoice_type' here

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['contract'].queryset = Contract.objects.filter(project=project)
