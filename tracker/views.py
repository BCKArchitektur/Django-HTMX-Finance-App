from django.shortcuts import render
from django.http import HttpResponse
from .models import Project , Logs , Contract , Section , Item , Task , ProjectPreset , UserPreset , Employee ,User , Client , SectionLibrary , Invoice
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .forms import LogForm  , Hiddenform ,ProjectForm, ClientForm , ContractForm , InvoiceForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, FloatField, Value
from django.db.models.functions import Cast
import datetime
from django.http import JsonResponse
from .models import Contract, Section , Task, Item
from django.utils import timezone
import pytz
from django.db.models import Sum, FloatField, F
from django.db.models import DateField
import json
from .models import ProjectPreset
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .forms import AddUsersForm, AddBudgetForm
from django.contrib import messages
from django.urls import reverse
from urllib.parse import urlencode
import docx
from docxtpl import DocxTemplate
import os
from django.conf import settings
from datetime import date
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import JsonResponse, Http404  # Import Http404
from decimal import Decimal  # Import Decimal for precision handling


@login_required
def toggle_dark_mode(request):
    user = request.user
    user.dark_mode = not user.dark_mode
    user.save()
    return JsonResponse({'dark_mode': user.dark_mode})

    
def login_page(request):
    return render(request,'projects/login_page.html')

def logout_page(request):
    return render(request,'projects/logout_page.html')


@login_required
def load_contracts(request):
    project_id = request.GET.get('project_id')
    if not project_id or not project_id.isdigit():
        return JsonResponse({'contracts': []})
    
    contracts = Contract.objects.filter(project__id=int(project_id), user=request.user).order_by('contract_name')
    contract_list = [{'id': contract.id, 'contract_name': contract.contract_name} for contract in contracts]
    return JsonResponse({'contracts': contract_list})


@login_required
def load_sections(request):
    contract_id = request.GET.get('contract_id')
    if not contract_id or not contract_id.isdigit():
        return JsonResponse({'sections': []})
    
    sections = Section.objects.filter(contract__id=int(contract_id), user=request.user).order_by('section_name')
    section_list = [{'id': section.id, 'section_name': section.section_name} for section in sections]
    return JsonResponse({'sections': section_list})


@login_required
def load_Items(request):
    section_id = request.GET.get('section_id')
    if not section_id or not section_id.isdigit():
        return JsonResponse({'Items': []})
    
    items = Item.objects.filter(section__id=int(section_id), users=request.user)
    item_list = [{'id': item.id, 'Item_name': item.Item_name} for item in items]
    return JsonResponse({'Items': item_list})

def load_tasks(request):
    item_id = request.GET.get('Item_id')
    
    # Check if Item_id is valid
    if not item_id or not item_id.isdigit():
        return HttpResponseBadRequest("Invalid Item ID")
    
    item_id = int(item_id)
    
    try:
        # Retrieve the Item object
        item = Item.objects.get(id=item_id)
        # Get the related tasks through the many-to-many relationship
        tasks = item.tasks.all()
        
        # Prepare the task list
        task_list = [{'id': task.id, 'task_name': task.task_name} for task in tasks]
        
        return JsonResponse({'tasks': task_list})
    
    except Item.DoesNotExist:
        return HttpResponseBadRequest("Item not found")


@login_required
def delete_log(request, log_id):

    
    # Force clean up of the log_id to remove commas
    try:
        cleaned_log_id = ''.join(log_id.split(','))  # Remove commas by splitting and rejoining
        cleaned_log_id = int(cleaned_log_id)  # Convert to integer
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Invalid log_id format'}, status=400)
    
    if request.method == 'POST':
        try:
            log = get_object_or_404(Logs, id=cleaned_log_id, user=request.user)  # Ensure the log belongs to the user
            
            log.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False}, status=400)



@login_required
def index(request):
    context = {
    }
    return render(request, 'tracker/index.html', context)

@login_required
def projects(request):
    projects = Project.objects.all()  # Show all projects
    clients = Client.objects.all()  # Assuming all clients should be shown
    project_form = ProjectForm()
    client_form = ClientForm()

    if request.method == 'POST':
        if 'project_name' in request.POST:
            project_form = ProjectForm(request.POST)
            if project_form.is_valid():
                project_form.save()
                return redirect('projects')
        elif 'client_name' in request.POST:
            client_form = ClientForm(request.POST)
            if client_form.is_valid():
                client_form.save()
                return redirect('projects')

    context = {
        'projects': projects.order_by('-project_no'),
        'clients': clients.order_by('-firm_name'),
        'project_form': project_form,
        'client_form': client_form,
    }
    return render(request, 'tracker/projects.html', context)


@csrf_exempt
@login_required
def delete_project(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        project.delete()
        return JsonResponse({'status': 'success'})
    return HttpResponseBadRequest("Invalid request")

@csrf_exempt
@login_required
def delete_client(request, client_id):
    if request.method == 'POST':
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        return JsonResponse({'status': 'success'})
    return HttpResponseBadRequest("Invalid request")




@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Fetch all projects to pass to the context
    all_projects = Project.objects.all()

    contracts = project.contract.all()
    clients = Client.objects.all()
    users = User.objects.all()
    contract_form = ContractForm()
    section_library = SectionLibrary.objects.all()  # Fetch all sections from the library
    invoices = Invoice.objects.filter(project=project)

    if request.method == 'POST':
        if 'project_name' in request.POST:
            return handle_project_form(request, project)
        elif 'contract_name' in request.POST and not request.POST.get('contract_id'):
            return handle_new_contract_form(request, project)
        elif request.POST.get('contract_id'):
            return handle_existing_contract_form(request, project)
        elif 'user' in request.POST:
            updated_users = request.POST.getlist('user')
            handle_user_updates(project, updated_users)
    else:
        form = ProjectForm(instance=project)

    # Get the VAT percentages for each contract
    vat_percentages = {contract.id: contract.vat_percentage for contract in contracts}

    context = {
        'form': form,
        'project': project,
        'contracts': contracts,
        'contract_form': contract_form,
        'clients': clients,
        'users': users,
        'section_library': section_library, 
        'invoices': invoices.order_by('-created_at'),
        'vat_percentages': vat_percentages,  # Pass VAT percentages to the template
        'all_projects': all_projects
    }
    return render(request, 'tracker/edit_project.html', context)



def handle_user_updates(project, updated_users):
    current_users = set(project.user.all())
    updated_users_set = set(User.objects.filter(id__in=updated_users))

    # Users to be added and removed
    users_to_add = updated_users_set - current_users
    users_to_remove = current_users - updated_users_set

    # Add users to project
    for user in users_to_add:
        project.user.add(user)
        for contract in project.contract.all():
            contract.user.add(user)
            for section in contract.section.all():
                section.user.add(user)
                for item in section.Item.all():
                    item.users.add(user)

    # Remove users from project
    for user in users_to_remove:
        project.user.remove(user)
        for contract in project.contract.all():
            contract.user.remove(user)
            for section in contract.section.all():
                section.user.remove(user)
                for item in section.Item.all():
                    item.users.remove(user)
    
    project.save()


def get_library_section(request, section_id):
    section = get_object_or_404(SectionLibrary, id=section_id)
    items = section.items.all()
    section_data = {
        'section_name': section.name,
        'items': [
            {
                'Item_name': item.name,
                'tasks': [{'task_name': task.name} for task in item.tasks.all()]
            }
            for item in items
        ]
    }
    return JsonResponse(section_data)


def handle_project_form(request, project):
    form = ProjectForm(request.POST, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, "Project updated successfully.")
    else:
        messages.error(request, "Error updating project: {}".format(form.errors))
    return redirect('edit_project', project_id=project.id)




import json
from django.shortcuts import redirect
from django.contrib import messages
from .models import Contract, Section, Item, Task


def handle_existing_contract_form(request, project):
    print("Request received for handling existing contract form.")

    # Retrieve contract ID
    contract_id = request.POST.get('contract_id')
    if not contract_id:
        print("No contract ID provided.")
        messages.error(request, "Contract ID is missing.")
        return redirect('edit_project', project_id=project.id)

    try:
        contract = Contract.objects.get(id=contract_id)
        print(f"Contract found: {contract}")
    except Contract.DoesNotExist:
        print(f"Contract with ID {contract_id} does not exist.")
        messages.error(request, "Contract not found.")
        return redirect('edit_project', project_id=project.id)

    # Validate contract form
    contract_form = ContractForm(request.POST, instance=contract)
    if not contract_form.is_valid():
        print(f"Contract form errors: {contract_form.errors}")
        messages.error(request, f"Error updating contract: {contract_form.errors}")
        return redirect('edit_project', project_id=project.id)

    # Save the contract form
    contract = contract_form.save()
    print("Contract form saved.")

    # Parse contract JSON
    contract_json = request.POST.get('contract_json')
    if not contract_json:
        print("No contract JSON data provided.")
        messages.error(request, "No contract JSON data provided.")
        return redirect('edit_project', project_id=project.id)

    try:
        contract_data = json.loads(contract_json)
        print(f"Parsed contract data: {contract_data}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        messages.error(request, "Error decoding the contract JSON data.")
        return redirect('edit_project', project_id=project.id)

    # Process sections
    sections_to_keep = []
    for section_data in sorted(contract_data.get('sections', []), key=lambda x: x.get('order', 0)):  # Sort sections by order
        section_id = section_data.get('id')
        section_name = section_data['section_name']
        section_billed_hourly = section_data.get('section_billed_hourly', False)
        section_order = section_data.get('order', 0)  # Get section order

        # Retrieve or create section
        if section_id and not str(section_id).startswith('new-'):
            section = Section.objects.filter(id=section_id).first()
            if section:
                print(f"Updating existing section: {section}")
                section.section_name = section_name
                section.section_billed_hourly = section_billed_hourly
                section.order = section_order  # Save section order
                section.save()
            else:
                print(f"Section with ID {section_id} not found. Creating new section.")
                section = Section.objects.create(
                    section_name=section_name,
                    section_billed_hourly=section_billed_hourly,
                    order=section_order
                )
        else:
            section = Section.objects.create(
                section_name=section_name,
                section_billed_hourly=section_billed_hourly,
                order=section_order
            )

        sections_to_keep.append(section)

        # Process items in the section
        items_to_keep = []
        for item_data in sorted(section_data.get('items', []), key=lambda x: x.get('order', 0)):  # Sort items by order
            item_id = item_data.get('id')
            item_name = item_data['Item_name']
            description = item_data.get('description', '')
            item_order = item_data.get('order', 0)  # Get item order

            # Retrieve or create item
            if item_id and not str(item_id).startswith('new-'):
                item = Item.objects.filter(id=item_id).first()
                if item:
                    print(f"Updating existing item: {item}")
                    item.Item_name = item_name
                    item.description = description
                    item.quantity = item_data.get('quantity', item.quantity)
                    item.unit = item_data.get('unit', item.unit)
                    item.rate = item_data.get('rate', item.rate)
                    item.order = item_order  # Save item order
                    item.save()
                else:
                    print(f"Item with ID {item_id} not found. Creating new item.")
                    item = Item.objects.create(
                        Item_name=item_name,
                        description=description,
                        quantity=item_data.get('quantity', 0),
                        unit=item_data.get('unit', 'Std'),
                        rate=item_data.get('rate', 0.0),
                        order=item_order
                    )
            else:
                item = Item.objects.create(
                    Item_name=item_name,
                    description=description,
                    quantity=item_data.get('quantity', 0),
                    unit=item_data.get('unit', 'Std'),
                    rate=item_data.get('rate', 0.0),
                    order=item_order
                )

            items_to_keep.append(item)

            # Process tasks for the item
            tasks_to_keep = []
            for task_data in item_data.get('tasks', []):
                task_name = task_data['task_name']

                # Create task (no ID means tasks are always new)
                task = Task.objects.create(task_name=task_name)
                tasks_to_keep.append(task)

            item.tasks.set(tasks_to_keep)  # Set all tasks for the item
            section.Item.add(item)  # Associate the item with the section

        section.Item.set(items_to_keep)  # Set all items for the section

    contract.section.set(sections_to_keep)  # Set all sections for the contract
    contract.save()

    # Associate contract with project
    project.contract.add(contract)
    project.save()

    print("Contract and project updated successfully.")
    messages.success(request, "Contract updated successfully.")
    return redirect('edit_project', project_id=project.id)






def handle_new_contract_form(request, project):
    contract_name = request.POST.get('contract_name')
    contract_json = request.POST.get('contract_json')
    contract_no = request.POST.get('contract_no')
    # Retrieve all users associated with the project
    user_ids = project.user.values_list('id', flat=True)
    
    # Debugging print statement
    print("POST data:", request.POST)

    # Create the Contract object with contract_no and contract_name
    contract = Contract.objects.create(
        contract_name=contract_name,
        contract_no = contract_no
    )
    contract.user.set(user_ids)

    
    # Debugging print statement to check if contract_json is None
    print("Received contract JSON:", contract_json)

    if contract_json:
        try:
            contract_data = json.loads(contract_json)
            
            # Debugging print statement to check the parsed JSON
            print("Parsed contract data:", contract_data)
            
            for section_data in contract_data.get('sections', []):
                section_name = section_data['section_name']
                section_billed_hourly = section_data.get('section_billed_hourly', False)
                
                # Create a new section regardless of the name
                section = Section.objects.create(
                    section_name=section_name,
                    section_billed_hourly=section_billed_hourly
                )
                print("Processed section:", section_name)  # Debugging line

                # Set project users to section
                section.user.set(user_ids)
                
                for item_data in section_data.get('items', []):
                    Item_name = item_data['Item_name']
                    description = item_data.get('description', '')  # Handle description
                    
                    # Create a new item regardless of the name
                    item = Item.objects.create(
                        Item_name=Item_name,
                        description=description
                    )
                    print("Processed item:", Item_name)  # Debugging line

                    # Set project users to item
                    item.users.set(user_ids)
                    
                    for task_data in item_data.get('tasks', []):
                        task_name = task_data['task_name']
                        task = Task.objects.create(task_name=task_name)
                        print("Processed task:", task_name)  # Debugging line
                        item.tasks.add(task)

                    section.Item.add(item)

                contract.section.add(section)

            contract.save()
            project.contract.add(contract)
            project.save()

            messages.success(request, "New contract added successfully.")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")  # Debugging line for JSON decode error
            messages.error(request, "Error decoding the contract JSON data.")
    else:
        messages.error(request, "No contract JSON data provided.")

    return redirect('edit_project', project_id=project.id)


def update_contract_details(request, contract):
    section_names = request.POST.getlist('section_name')
    Item_names = request.POST.getlist('Item_name')
    task_names = request.POST.getlist('task_name')

    contract.section.clear()
    for section_name in section_names:
        section, _ = Section.objects.get_or_create(section_name=section_name)
        section.Item.clear()
        for Item_name in Item_names:
            item, _ = Item.objects.get_or_create(Item_name=Item_name)
            item.tasks.clear()
            for task_name in task_names:
                task, _ = Task.objects.get_or_create(task_name=task_name)
                item.tasks.add(task)
            section.Item.add(item)
        contract.section.add(section)
    contract.save()


@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            # Construct the URL with the query parameter
            url = reverse('projects') + '?' + urlencode({'tab': 'clients'})
            return redirect(url)
    else:
        form = ClientForm(instance=client)
    return render(request, 'tracker/edit_client.html', {'form': form, 'client': client})



@login_required
def dashboard(request):
    context = {
    }
    return render(request, 'tracker/dashboard.html', context)

#view to get current time
def get_berlin_time():
    berlin_timezone = pytz.timezone('Europe/Berlin')
    current_time = timezone.now()
    localized_time = current_time.astimezone(berlin_timezone)
    formatted_time = localized_time.strftime('%d/%m/%y %H:%M:%S')
    return formatted_time

#Log view to create log
@login_required
def log_create_compact(request):
    projects = Project.objects.filter(user=request.user)
    project_presets = ProjectPreset.objects.filter(user=request.user)
    logs = Logs.objects.filter(user=request.user).order_by('-log_timestamps')

    today = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d')
    logs_today = Logs.objects.filter(user=request.user, log_timestamps__startswith=today)
    total_hours_today = logs_today.annotate(
        numeric_time=Cast('log_time', FloatField())
    ).aggregate(total_time=Sum('numeric_time'))['total_time'] or 0

    # Get the employee's assigned hours
    employee = get_object_or_404(Employee, user=request.user)
    
    # Determine today's day of the week
    day_of_week = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).weekday()

    # Mapping of day of the week to the corresponding hours assigned variable
    hours_assigned_mapping = {
        0: employee.hours_assigned_monday,
        1: employee.hours_assigned_tuesday,
        2: employee.hours_assigned_wednesday,
        3: employee.hours_assigned_thursday,
        4: employee.hours_assigned_friday,
    }

    hours_assigned_today = hours_assigned_mapping.get(day_of_week, 0)

    # Calculate the progress percentage
    progress_percentage = (total_hours_today / hours_assigned_today) * 100 if hours_assigned_today > 0 else 0

    form = Hiddenform(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        log_project_name = form.cleaned_data['log_project_name']
        log_contract_id = form.cleaned_data['log_contract'].replace(",", "") # Use the contract ID
        log_tasks = form.cleaned_data['log_tasks']
        log_section_id = form.cleaned_data['log_section'].replace(",", "") # Use the section ID
        print(f"log_section_id: {log_section_id}")  # Debugging line
        log_item_id = form.cleaned_data['log_Item'].replace(",", "")  # Use the item ID
        log_time = form.cleaned_data['log_time']
        log_timestamps = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S')
        
        # Fetch by ID
        log_project = get_object_or_404(Project, project_name=log_project_name)
        log_contract = get_object_or_404(Contract, id=log_contract_id)  # Fetch by ID instead of name
        log_section = get_object_or_404(Section, id=log_section_id)  # Fetch by ID instead of name
        log_item = get_object_or_404(Item, id=log_item_id)  # Fetch by ID instead of name

        log_entry = Logs.objects.create(
            log_project_name=log_project_name,
            log_contract=log_contract,
            log_section=log_section,
            log_Item=log_item,
            log_time=log_time,
            log_timestamps=log_timestamps,
            log_tasks=log_tasks,
            user=request.user
        )
        log_entry.save()
        return redirect('log_create_compact')

    context = {
        'project_presets': project_presets,
        'form': form,
        'logs': logs,
        'total_hours_today': total_hours_today,
        'hours_assigned_today': hours_assigned_today,
        'progress_percentage': progress_percentage,
        'projects': projects,
        'employee': employee,
    }
    return render(request, 'tracker/log_create_compact.html', context)



@login_required
def log_create(request):
    projects = Project.objects.filter(user=request.user)
    logs = Logs.objects.filter(user=request.user).order_by('-log_timestamps')
    today = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d')
    logs_today = Logs.objects.filter(user=request.user, log_timestamps__startswith=today)
    total_hours_today = logs_today.annotate(
        numeric_time=Cast('log_time', FloatField())
    ).aggregate(total_time=Sum('numeric_time'))['total_time'] or 0

    # Get the employee's assigned hours
    employee = get_object_or_404(Employee, user=request.user)
    
    # Determine today's day of the week
    day_of_week = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).weekday()

    # Mapping of day of the week to the corresponding hours assigned variable
    hours_assigned_mapping = {
        0: employee.hours_assigned_monday,
        1: employee.hours_assigned_tuesday,
        2: employee.hours_assigned_wednesday,
        3: employee.hours_assigned_thursday,
        4: employee.hours_assigned_friday,
    }

    hours_assigned_today = hours_assigned_mapping.get(day_of_week, 0)

    # Calculate the progress percentage
    progress_percentage = (total_hours_today / hours_assigned_today) * 100 if hours_assigned_today > 0 else 0

    form = LogForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        log_project_name = form.cleaned_data['log_project_name'].project_name
        log_contract = form.cleaned_data['log_contract']
        log_tasks = form.cleaned_data['log_tasks']
        log_section = form.cleaned_data['log_section']
        print(f"log_section: {log_section}")  # Debugging line
        log_Item = form.cleaned_data['log_Item']
        log_time = form.cleaned_data['log_time']


        # Get the submitted date and keep the current time
        submitted_date = form.cleaned_data['log_date'] or today  # Fallback to today's date if empty
        current_time = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%H:%M:%S')
        log_timestamps = f"{submitted_date} {current_time}"
        
        # Create the log entry
        log_entry = Logs.objects.create(
            log_project_name=log_project_name,
            log_contract=log_contract,
            log_section=log_section,
            log_Item=log_Item,
            log_time=log_time,
            log_timestamps=log_timestamps,
            log_tasks=log_tasks,
            user=request.user
        )
        log_entry.save()

        project = form.cleaned_data['log_project_name']
        default_contract = form.cleaned_data['log_contract']
        default_section = form.cleaned_data['log_section']
        default_Item = form.cleaned_data['log_Item']

        user_presets = ProjectPreset.objects.filter(user=request.user)
        if user_presets.count() >= 4:
            # Delete the oldest preset specific to the user
            oldest_preset = user_presets.order_by('id').first()
            oldest_preset.delete()

        # Check if an existing preset with the same values already exists
        existing_preset = ProjectPreset.objects.filter(
            user=request.user,
            project=project,
            default_contract=default_contract,
            default_section=default_section,
            default_Item=default_Item
        ).exists()

        # Only create a new preset if no existing one is found
        if not existing_preset:
            ProjectPreset.objects.create(
                user=request.user,
                project=project,
                default_contract=default_contract,
                default_section=default_section,
                default_Item=default_Item,
            )

        return redirect('log_create')
    else:
        form = LogForm(user=request.user)

    context = {
        'form': form,
        'logs': logs,
        'total_hours_today': total_hours_today,
        'hours_assigned_today': hours_assigned_today,
        'progress_percentage': progress_percentage,
        'projects': projects.order_by('-project_no'),
        'date_override': employee.date_override,
    }
    return render(request, 'tracker/log_create.html', context)




@login_required
def project_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    contracts = project.contract_set.all()

    contract_data = []
    for contract in contracts:
        sections = contract.section_set.all()
        for section in sections:
            # Mock data for used budget, replace with actual logic
            used_budget = section.allocated_budget * 1.2  # Example logic
            contract_data.append({
                'contract_name': contract.contract_name,
                'section_name': section.section_name,
                'allocated_budget': section.allocated_budget,
                'used_budget': used_budget
            })

    response = {
        'project_name': project.project_name,
        'contracts': contract_data
    }

    if request.is_ajax():
        return JsonResponse(response)
    else:
        return render(request, 'tracker/project_details.html', {'project': project, 'contracts': contract_data})


@login_required
def add_project(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_address = request.POST.get('project_address', '')
        new_project = Project.objects.create(
            user=request.user,
            project_name=project_name,
            project_address=project_address,
            project_no="PN-" + str(Project.objects.count() + 1)  # Example project number
        )
        return redirect('projects')
    return redirect('projects')






def load_contract_data(request):
    contract_id = request.GET.get('contract_id')
    contract = get_object_or_404(Contract, id=contract_id)
    
    # Ensure the contract belongs to at least one project
    project_id = contract.project_set.first().id if contract.project_set.exists() else None
    if not project_id:
        return JsonResponse({'error': 'Contract does not belong to any project'}, status=400)

    # Fetch all previous invoices for this project
    previous_invoices = Invoice.objects.filter(project_id=project_id)

    # Check if any invoices exist
    invoices_exist = previous_invoices.exists()

    users = list(User.objects.all().values('id', 'username'))

    # Retrieve and sort sections by their 'order' attribute (default to 0 if missing)
    sections = sorted(contract.section.all(), key=lambda s: getattr(s, 'order', 0))

    section_data = []

    for section in sections:
        # Retrieve and sort items within each section by their 'order' attribute (default to 0 if missing)
        items = sorted(section.Item.all(), key=lambda i: getattr(i, 'order', 0))

        item_data = []
        for item in items:
            # Calculate the total provided quantity for this item from previous invoices
            total_provided_quantity = sum(
                invoice.provided_quantities.get(str(item.id), {}).get('quantity', 0)
                for invoice in previous_invoices
            )
            available_quantity = item.quantity - total_provided_quantity

            item_data.append({
                'order': getattr(item, 'order', 0),  # Get the 'order' attribute, default to 0
                'id': item.id,
                'Item_name': item.Item_name,
                'description': item.description,
                'quantity': item.quantity,
                'available_quantity': available_quantity,
                'unit': item.unit,
                'rate': item.rate,
                'total': item.total,
                'users': list(item.users.values_list('id', flat=True)),  # Get associated users
                'tasks': list(item.tasks.values('id', 'task_name')),  # Get associated tasks
            })

        section_data.append({
            'order': getattr(section, 'order', 0),  # Get the 'order' attribute, default to 0
            'id': section.id,  # Include the section ID
            'section_name': section.section_name,
            'section_billed_hourly': section.section_billed_hourly,
            'items': item_data,
        })

    contract_data = {
        'contract_name': contract.contract_name,
        'contract_no':contract.contract_no,
        'users': users,
        'sections': section_data,
        'additional_fee_percentage': contract.additional_fee_percentage,
        'vat_percentage': contract.vat_percentage,  # Add VAT percentage to the response
        'invoices_exist': invoices_exist,  # Add whether invoices exist to the response
    }

    return JsonResponse(contract_data)




def check_task_name(request):
    task_name = request.GET.get('task_name', None)
    is_taken = Task.objects.filter(task_name__iexact=task_name).exists()
    data = {
        'is_taken': is_taken,
        'message': 'Task name is already taken.' if is_taken else 'Task name is available.'
    }
    return JsonResponse(data)

def check_section_name(request):
    section_name = request.GET.get('section_name', None)
    is_taken = Section.objects.filter(section_name__iexact=section_name).exists()
    data = {
        'is_taken': is_taken,
        'message': 'Section name is already taken.' if is_taken else 'Section name is available.'
    }
    return JsonResponse(data)

def check_Item_name(request):
    Item_name = request.GET.get('Item_name', None)
    is_taken = Item.objects.filter(Item_name__iexact=Item_name).exists()
    data = {
        'is_taken': is_taken,
        'message': 'Item name is already taken.' if is_taken else 'Item name is available.'
    }
    return JsonResponse(data)

def check_contract_name(request):
    contract_name = request.GET.get('contract_name', None)
    is_taken = Contract.objects.filter(contract_name__iexact=contract_name).exists()
    data = {
        'is_taken': is_taken,
        'message': 'Contract name is already taken.' if is_taken else 'Contract name is available.'
    }
    return JsonResponse(data)





@csrf_exempt
@login_required
def add_users(request):
    if request.method == 'POST':
        contract_id = request.POST.get('contract_id')
        contract = get_object_or_404(Contract, id=contract_id)
        
        for section in contract.section.all():
            for item in section.Item.all():
                for user in User.objects.all():
                    user_checkbox = f'user_item_{user.id}_{item.id}'
                    if user_checkbox in request.POST:
                        item.users.add(user)
                    else:
                        item.users.remove(user)

        # Now update the users of the sections based on the users of their items
        for section in contract.section.all():
            section_users = set()
            for item in section.Item.all():
                section_users.update(item.users.all())
            section.user.set(section_users)

        # Update the users of the contract based on the users of its sections
        contract_users = set()
        for section in contract.section.all():
            contract_users.update(section.user.all())
        contract.user.set(contract_users)

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)






@csrf_exempt
@login_required
def add_budget(request):
    if request.method == 'POST':
        contract_id = request.POST.get('contract_id')
        if not contract_id:
            return JsonResponse({'error': 'Missing contract ID'}, status=400)

        contract = get_object_or_404(Contract, id=contract_id)

        # Handle additional fee percentage
        additional_fee_percentage = request.POST.get('additional_fee_percentage')
        try:
            contract.additional_fee_percentage = float(additional_fee_percentage)
        except (ValueError, TypeError):
            contract.additional_fee_percentage = 0.0

        # Handle VAT percentage
        vat_percentage = request.POST.get('vat_percentage')
        try:
            contract.vat_percentage = float(vat_percentage)
        except (ValueError, TypeError):
            contract.vat_percentage = 0.0

        # Handle the sections and items
        for section in contract.section.all():
            for item in section.Item.all():
                quantity_key = f'quantity_{item.id}'
                unit_key = f'unit_{item.id}'
                rate_key = f'rate_{item.id}'
                if quantity_key in request.POST and rate_key in request.POST:
                    try:
                        quantity = parse_german_number((request.POST[quantity_key]))
                        unit = request.POST[unit_key]
                        rate = parse_german_number((request.POST[rate_key]))
                        item.quantity = quantity
                        item.unit = unit
                        item.rate = rate
                        item.total = quantity * rate
                        item.save()
                        print(f"Received item details: quantity={quantity}, unit={unit}, rate={rate}")  # Debug line
                    except (ValueError, Item.DoesNotExist):
                        continue

        # Save the contract with the updated VAT and additional fee percentages
        contract.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def parse_german_number(number_string):
    try:
        # Convert German-style number (1.000,50) to Python float (1000.50)
        return float(number_string.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0



def load_item_users(request):
    item_id = request.GET.get('item_id')
    item = get_object_or_404(Item, id=item_id)
    users = list(item.users.values_list('id', flat=True))
    return JsonResponse({'users': users})

def load_item_budget(request):
    item_id = request.GET.get('item_id')
    item = get_object_or_404(Item, id=item_id)
    budget = item.budget
    return JsonResponse({'budget': budget})

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Item

def add_users_to_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        item.users.set(user_ids)
        item.save()  # This will trigger the cascading update
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'}, status=400)

def get_project_users(request):
    project_id = request.GET.get('project_id')
    print(f"Received project_id: {project_id}")  # Debugging line
    try:
        project = Project.objects.get(id=project_id)
        users = project.user.all()
        user_list = [{'id': user.id, 'username': user.username} for user in users]
        return JsonResponse({'project_users': user_list})
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@login_required
def delete_contract(request, contract_id):
    if request.method == 'POST':
        contract = get_object_or_404(Contract, id=contract_id)
        project_id = contract.project_set.first().id  # Assuming a contract belongs to at least one project
        contract.delete()
        messages.success(request, 'Contract deleted successfully.')
        return redirect(reverse('edit_project', args=[project_id]))
    return JsonResponse({'error': 'Invalid request'}, status=400)



def generate_word_document(request, contract_id):
    template_name = request.GET.get('template_name', 'Kost_De.docx')
    valid_until = request.GET.get('valid_until')
    terms_conditions = request.GET.get('terms_conditions')

    print(f"Template Name: {template_name}")
    print(f"Valid Until: {valid_until}")

    contract = get_object_or_404(Contract, id=contract_id)
    project = contract.project_set.first()  # Assuming a contract belongs to at least one project
    client = project.client_name  # Assuming client_name is a related model, not just a field

    # Construct the template path using the template name from the URL parameter
    template_path = os.path.join(r'C:\Users\BCK-CustomApp\Documents\GitHub\Django-HTMX-Finance-App\templates\estimates', template_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at {template_path}")

    doc = DocxTemplate(template_path)

    # Ensure client details are accessed correctly
    client_name = getattr(client, 'client_name', 'Unknown')
    firm_name = getattr(client, 'firm_name', 'Unknown')
    street_address = getattr(client, 'street_address', 'Unknown')
    city = getattr(client, 'city', 'Unknown')
    postal_code = getattr(client, 'postal_code', 'Unknown')
    country = getattr(client.country, 'name', 'Unknown') if hasattr(client, 'country') else 'Unknown'

    # Calculate contract details with serial numbers
    contract_sections = []
    sum_of_items = Decimal(0)  # Ensure this is a Decimal for accurate calculations

    # Initialize section counter
    section_counter = 1

    # Flag for checking if the template is in English
    is_english_template = template_name in ['BCK_En.docx', 'Kost_En.docx']

    for section in sorted(contract.section.all(), key=lambda s: getattr(s, 'order', 0)):  # Sort sections by 'order'
        section_total = Decimal(0)
        items = []

        # Initialize item counter for the current section
        item_counter = 1

        for item in sorted(section.Item.all(), key=lambda i: getattr(i, 'order', 0)):  # Sort items by 'order'
            item_total = Decimal(item.quantity) * Decimal(item.rate)

            # Check if template is in English and replace units if needed
            unit = item.unit
            if is_english_template:
                if unit == 'Psch':
                    unit = 'Lumpsum'
                elif unit == 'Stk':
                    unit = 'Piece'
                elif unit == 'Std':
                    unit = 'Hour'

            item_data = {
                'Item_serial': f"{section_counter}.{item_counter}",
                'Item_name': item.Item_name,
                'quantity': f"{item.quantity:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'unit': unit,
                'rate': f"{Decimal(item.rate):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'total': f"{item_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }
            if item.description:
                item_data['description'] = item.description
            items.append(item_data)
            section_total += item_total

            # Increment item counter
            item_counter += 1

        contract_sections.append({
            'section_serial': section_counter,
            'section_name': section.section_name,
            'net_section': f"{section_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Item': items
        })
        sum_of_items += section_total

        # Increment section counter
        section_counter += 1


    additional_fee_percentage = Decimal(contract.additional_fee_percentage)
    additional_fee_value = (sum_of_items * additional_fee_percentage) / Decimal(100)
    net_contract = sum_of_items + additional_fee_value

    # Convert vat_percentage to float
    vat_percentage = float(contract.vat_percentage) / 100
    tax = float(net_contract) * vat_percentage
    gross_contract = net_contract + Decimal(tax)

    # Context for template
    context = {
        # other context data
        'contract_name': contract.contract_name,
        'contract_no': contract.contract_no,
        'project_name': project.project_name,
        'project_no': project.project_no,
        'client_name': client_name,
        'client_firm': firm_name,
        'client_address': f"{street_address}\n{postal_code} {city} \n{country}",
        'contract_sections': contract_sections,
        'sum_of_items': f"{sum_of_items:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'net_contract': f"{net_contract:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'tax': f"{Decimal(tax):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'gross_contract': f"{gross_contract:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'today_date': date.today().strftime('%d.%m.%Y'),
        'valid_until': valid_until if not valid_until else date.fromisoformat(valid_until).strftime('%d.%m.%Y'),
        'vat_percentage': f"{vat_percentage * 100:.2f}",  # Pass VAT percentage to the template if needed
        'terms_conditions': terms_conditions,
    }

    # Only add the additional fee to the context if it's greater than 0
    if additional_fee_percentage > 0:
        context.update({
            'additional_fee_percentage': f"{additional_fee_percentage:.2f}",
            'additional_fee_value': f"{additional_fee_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        })

    # Print the context for debugging
    import pprint
    pprint.pprint(context)

    # Render the document with context
    doc.render(context)

    # Create HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    # Determine the prefix based on the template type
    prefix = "BCK" if "BCK" in template_name else "KOST"

    # Build the file name in the desired format
    file_name = f"{contract.contract_no} {prefix} {project.project_name[:6]} AN {contract.contract_name}.docx"


    # Set the Content-Disposition header for file download
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    doc.save(response)

    return response





from django.contrib import messages

@login_required
def create_invoice(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    contracts = project.contract.all()

    # Assuming the user will select a contract, and you'll fetch the first contract as a default
    selected_contract = contracts.first() if contracts else None
    additional_fee_percentage = selected_contract.additional_fee_percentage if selected_contract else 0
    vat_percentage = selected_contract.vat_percentage if selected_contract else 0  # Fetch VAT percentage from the contract

    if request.method == 'POST':
        form = InvoiceForm(request.POST, project=project)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.project = project
            invoice.provided_quantities = json.loads(request.POST.get('provided_quantities'))
            invoice.save()

            # Add a success message
            messages.success(request, 'Invoice created successfully.')

            # Redirect to the edit project page with the invoices tab open
            return HttpResponseRedirect(reverse('edit_project', args=[project_id]) + '?tab=invoices')
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = InvoiceForm(project=project)

    return render(request, 'tracker/create_invoice.html', {
        'form': form,
        'project': project,
        'contracts': contracts,
        'additional_fee_percentage': additional_fee_percentage,
        'vat_percentage': vat_percentage  # Pass VAT percentage to the template
    })




def calculate_available_quantity(project, item):
    all_invoices = Invoice.objects.filter(project=project)
    total_quantity_invoiced = sum(
        json.loads(invoice.provided_quantities).get(str(item.id), {}).get('quantity', 0)
        for invoice in all_invoices
    )
    return item.quantity - total_quantity_invoiced


# View for deleting an invoice
@login_required
def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    project_id = invoice.project.id  # Assuming an invoice belongs to a project
    invoice.delete()

    # Redirect to the edit project page with the invoices tab open
    return redirect(reverse('edit_project', args=[project_id]) + '?tab=invoices')




@login_required
def view_invoice(request, invoice_id):
    try:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        project = invoice.project
        contract = invoice.contract

        # Assume provided_quantities is a JSON string field in the Invoice model
        try:
            provided_quantities_data = invoice.provided_quantities
        except ValueError as e:
            print(f"Error parsing provided_quantities: {e}")
            return JsonResponse({'error': 'Invalid data format for provided quantities'}, status=400)

        provided_quantities = []
        sum_of_items = Decimal('0.00')
        for item_id, details in provided_quantities_data.items():
            try:
                # Fetch the item using the item ID
                item = Item.objects.get(id=item_id)
                
                # Find the section to which this item belongs within the contract
                section = Section.objects.filter(Item=item, contract=contract).first()
                section_name = section.section_name if section else "Unknown Section"

                rate = Decimal(details['rate'])
                quantity = Decimal(details['quantity'])
                total = rate * quantity
                sum_of_items += total

                provided_quantities.append({
                    'section_name': section_name,
                    'item_name': item.Item_name,
                    'unit': item.unit,
                    'rate': str(rate),
                    'quantity': str(quantity),
                    'total': str(total),
                })
            except Item.DoesNotExist:
                print(f"Item with id {item_id} does not exist.")
                rate = Decimal(details['rate'])
                quantity = Decimal(details['quantity'])
                total = rate * quantity
                sum_of_items += total

                provided_quantities.append({
                    'section_name': 'Unknown Section',
                    'item_name': f'Unknown Item (ID: {item_id})',
                    'unit': 'Unknown Unit',
                    'rate': str(rate),
                    'quantity': str(quantity),
                    'total': str(total),
                })

        # Calculate the additional fee, invoice net, VAT, and gross invoice values
        additional_fee_percentage = Decimal(contract.additional_fee_percentage or 0)
        vat_percentage = Decimal(contract.vat_percentage ) 
        additional_fee_value = (sum_of_items * additional_fee_percentage) / Decimal(100)
        invoice_net = sum_of_items + additional_fee_value
        tax_value = (invoice_net * vat_percentage) / Decimal(100)
        invoice_gross = invoice_net + tax_value

        data = {
            'project_name': project.project_name,
            'contract_name': contract.contract_name,
            'additional_fee_percentage': str(additional_fee_percentage),
            'provided_quantities': provided_quantities,
            'invoice_net': str(invoice_net),
            'tax_value': str(tax_value),
            'invoice_gross': str(invoice_gross),
            'vat_percentage': str(vat_percentage),  # Include VAT percentage in the response
            'amount_received':invoice.amount_received
        }

        return JsonResponse(data)

    except Http404 as e:
        print(f"Invoice or related data not found: {e}")
        return JsonResponse({'error': 'Invoice not found'}, status=404)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


from django.utils.dateparse import parse_date

def download_invoice(request, invoice_id):
    # Fetch the invoice, project, and contract
    invoice = get_object_or_404(Invoice, id=invoice_id)
    project = invoice.project
    contract = invoice.contract
    client = project.client_name

    # Get the template name and date range from the request
    template_name = request.GET.get('invoice_template_name', 'inv_BCK_De.docx')
    print(f"Template name from modal: {template_name}")
    
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Parse the date strings into date objects
    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None


    # Initialize the sections dictionary and sum_of_items
    sections = {}
    sum_of_items = Decimal('0.00')

    # Section counter
    section_counter = 1

    # Fetch provided quantities and related items and sections
    provided_quantities = invoice.provided_quantities  # Assuming this is a dictionary
    for item_id, details in provided_quantities.items():
        item = get_object_or_404(Item, id=item_id)
        section = item.section_set.first()  # Assuming each item belongs to one section
        section_name = section.section_name if section else "Unknown Section"
        item_total = Decimal(details['quantity']) * Decimal(details['rate'])

        if section_name not in sections:
            sections[section_name] = {
                'section_number': section_counter,
                'items': []
            }
            section_counter += 1

        # Calculate item number (e.g., 1.1, 1.2, 2.1, etc.)
        item_number = f"{sections[section_name]['section_number']}.{len(sections[section_name]['items']) + 1}"

        sections[section_name]['items'].append({
            'item_number': item_number,
            'item_name': item.Item_name,
            'unit': item.unit,
            'rate': f"{Decimal(details['rate']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'quantity': details['quantity'],
            'total': f"{item_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'description': item.description if item.description else None,
        })

        sum_of_items += item_total

    # Calculate additional fee and taxes
    additional_fee_percentage = Decimal(contract.additional_fee_percentage)
    additional_fee_value = (sum_of_items * additional_fee_percentage) / Decimal(100)
    invoice_net = sum_of_items + additional_fee_value
    vat_percentage = Decimal(contract.vat_percentage) / Decimal(100)  # Use VAT from contract
    tax_value = invoice_net * vat_percentage
    invoice_gross = invoice_net + tax_value

    # Fetch all previous invoices for the same project, based on created_at comparison
    previous_invoices = Invoice.objects.filter(
        project=project,
        created_at__lt=invoice.created_at  # Only include invoices created before the current invoice
    ).order_by('created_at')

    # Prepare previous invoices data and calculate totals
    total_invoice_gross = Decimal('0.00')
    total_amount_paid = Decimal('0.00')

    previous_invoices_data = []

    for inv in previous_invoices:
        inv_gross = Decimal(inv.invoice_net) * (1 + vat_percentage)
        inv_paid = Decimal(inv.amount_received)

        total_invoice_gross += inv_gross
        total_amount_paid += inv_paid

        previous_invoices_data.append({
            'invoice_title': inv.title,
            'created_at': timezone.localtime(inv.created_at).strftime('%d.%m.%Y'),  # German format with time
            'invoice_net': f"{Decimal(inv.invoice_net):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'invoice_tax%': vat_percentage,
            'invoice_tax': f"{(Decimal(inv.invoice_net) * vat_percentage):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'invoice_gross': f"{inv_gross:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'amount_paid': f"{inv_paid:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        })

    # Add the current invoice's gross to the total
    total_invoice_gross += invoice_gross

    # Calculate the amount to be paid (excluding the current invoice's amount received)
    invoice_tobepaid = total_invoice_gross - total_amount_paid

    # Prepare the context for the template
    context = {
        'client_name': client.client_name if client else "Unknown",
        'client_address': f"{client.street_address}\n{client.postal_code} {client.city} \n{client.country.name}",
        'created_at': timezone.localtime(invoice.created_at).strftime('%d.%m.%Y'),  # German format with time
        'project_no': project.project_no,
        'project_name': project.project_name,
        'invoice_title': invoice.title,
        'contract_name': contract.contract_name,
        'sections': sections,  # Organized by section
        'sum_of_items': f"{sum_of_items:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'invoice_net': f"{invoice_net:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'vat_percentage': vat_percentage,  # Pass this to template to multiply by 100
        'tax': f"{tax_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'invoice_gross': f"{invoice_gross:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'previous_invoices': previous_invoices_data,  # Ensure this is always a list
        'total_invoice_gross': f"{total_invoice_gross:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'total_amount_paid': f"{total_amount_paid:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'invoice_tobepaid': f"{invoice_tobepaid:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'invoice_type':invoice.invoice_type,
        'from_date': from_date.strftime('%d.%m.%Y') if from_date else None,
        'to_date': to_date.strftime('%d.%m.%Y') if to_date else None,
        'client_firm':client.firm_name
    }

    if additional_fee_percentage > 0:
        context.update({
            'additional_fee_percentage': f"{additional_fee_percentage:.2f}",
            'additional_fee_value': f"{additional_fee_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        })

    # Print context for debugging
    import pprint
    pprint.pprint(context)

    # Path to the invoice template
    # template_path = r'Z:\02_Zubehör\3_Vorlagen\BCK App Templates\Invoice_Template.docx'

    # Construct the template path using the selected template name from the request
    template_path = os.path.join(r'C:\Users\BCK-CustomApp\Documents\GitHub\Django-HTMX-Finance-App\templates\invoices', template_name)


    # Load the template
    doc = DocxTemplate(template_path)

    # Render the document with the context
    doc.render(context)

    # Create the HTTP response with the rendered document
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=invoice_{invoice.title}_{invoice.project}.docx'
    
    # Save the document to the response
    doc.save(response)

    return response





def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        amount_received = float(request.POST.get('amount_received'))
        invoice.amount_received = amount_received
        invoice.save()

        # Add a success message
        messages.success(request, 'Payment recorded successfully.')

        # Redirect to the project page with the invoices tab active
        return redirect(reverse('edit_project', args=[invoice.project.id]) + '?tab=invoices')

    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.http import JsonResponse
from .models import EstimateInvoiceSettings, Project

def get_new_contract_number(request, project_id):
    try:
        # Fetch the current consecutive number
        settings = EstimateInvoiceSettings.objects.first()
        if not settings:
            return JsonResponse({"error": "Settings not configured."}, status=400)

        consecutive_no = settings.consecutive_start_no

        # Fetch the project
        project = Project.objects.get(id=project_id)
        project_no = project.project_no

        # Combine consecutive_no and project_no
        contract_no = f"{consecutive_no}-{project_no}"

        return JsonResponse({"contract_no": contract_no})
    except Project.DoesNotExist:
        return JsonResponse({"error": "Project not found."}, status=404)


from bs4 import BeautifulSoup

@csrf_exempt
def update_scope(request, contract_id):
    if request.method == 'POST':
        scope_of_work = request.POST.get('scope_of_work', '')
        print(f"Raw scope_of_work: {scope_of_work}")

        # Validate HTML
        try:
            soup = BeautifulSoup(scope_of_work, 'html.parser')
            sanitized_html = str(soup)  # Ensure valid HTML structure
            print(f"Sanitized HTML: {sanitized_html}")
        except Exception as e:
            print(f"HTML parsing error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid HTML content'}, status=400)

        try:
            contract = Contract.objects.get(id=contract_id)
            contract.scope_of_work = sanitized_html
            contract.save()
            return JsonResponse({'status': 'success', 'message': 'Scope updated successfully'})
        except Exception as e:
            print(f"Database save error: {e}")
            return JsonResponse({'status': 'error', 'message': f'Error saving contract: {str(e)}'}, status=500)
