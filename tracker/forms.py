from django import forms
from .models import Project, Contract, Section, Task, Logs, Item


class LogForm(forms.Form):
    log_project_name = forms.ModelChoiceField(queryset=Project.objects.none(), label="Project")
    log_contract = forms.ModelChoiceField(queryset=Contract.objects.none(), required=True, label="Contract")
    log_section = forms.ModelChoiceField(queryset=Section.objects.none(), required=True, label="Section")
    log_Item = forms.ModelChoiceField(queryset=Item.objects.none(), required=True, label="Item")
    log_tasks = forms.CharField(widget=forms.HiddenInput(), label="Tasks", required=True)

    TIME_CHOICES = (
        ('', '--------'),
        ('0.25', '15min'),
        ('0.50', '30min'),
        ('0.75', '45min'),
        ('1.00', '1hr'),
        ('1.50', '1hr 30min'),
        ('2.00', '2hr'),
        ('2.50', '2hr 30min'),
        ('3.00', '3hr'),
        ('3.50', '3hr 30min'),
        ('4.00', '4hr'),
        ('4.50', '4hr 30min'),
        ('5.00', '5hr'),
        ('5.50', '5hr 30min'),
        ('6.00', '6hr'),
        ('6.50', '6hr 30min'),
        ('7.00', '7hr'),
        ('7.50', '7hr 30min'),
        ('8.00', '8hr'),
    )
    log_time = forms.ChoiceField(choices=TIME_CHOICES, label="Time", initial='', widget=forms.Select(), required=True)

    widgets = {
            'log_project_name': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
            'log_contract': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
            'log_section': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
            'log_Item': forms.Select(attrs={'class': 'select select-bordered w-full max-w-xs'}),
            'log_time': forms.NumberInput(attrs={'class': 'input input-bordered w-full max-w-xs'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LogForm, self).__init__(*args, **kwargs)
        self.fields['log_project_name'].queryset = Project.objects.filter(user=user)
        if self.is_bound:
            self.fields['log_contract'].queryset = Contract.objects.filter(project=self.data.get('log_project_name'))
            self.fields['log_section'].queryset = Section.objects.filter(contract=self.data.get('log_contract'))
            self.fields['log_Item'].queryset = Item.objects.filter(section=self.data.get('log_section'))
        else:
            self.fields['log_contract'].queryset = Contract.objects.none()
            self.fields['log_section'].queryset = Section.objects.none()
            self.fields['log_Item'].queryset = Item.objects.none()