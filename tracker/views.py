from django.shortcuts import render
from django.http import HttpResponse
from .models import Project , Logs , Contract , Section , Item , Task , ProjectPreset , UserPreset , Employee ,User , Client , SectionLibrary
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .forms import LogForm  , Hiddenform ,ProjectForm, ClientForm , ContractForm
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

def load_contracts(request):
    project_id = request.GET.get('project_id')
    if not project_id or not project_id.isdigit():
        return HttpResponseBadRequest("Invalid project ID")
    contracts = Contract.objects.filter(project__id=int(project_id)).order_by('contract_name')
    contract_list = [{'id': contract.id, 'contract_name': contract.contract_name} for contract in contracts]
    return JsonResponse({'contracts': contract_list})

def load_sections(request):
    contract_id = request.GET.get('contract_id')
    if not contract_id or not contract_id.isdigit():
        return HttpResponseBadRequest("Invalid contract ID")
    sections = Section.objects.filter(contract__id=int(contract_id)).order_by('section_name')
    section_list = [{'id': section.id, 'section_name': section.section_name} for section in sections]
    return JsonResponse({'sections': section_list})

def load_Items(request):
    section_id = request.GET.get('section_id')
    if not section_id or not section_id.isdigit():
        return HttpResponseBadRequest("Invalid section ID")
    Items = Item.objects.filter(section__id=int(section_id))
    Item_list = [{'id': Item.id, 'Item_name': Item.Item_name} for Item in Items]
    return JsonResponse({'Items': Item_list})

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
    if request.method == 'POST':
        log = get_object_or_404(Logs, id=log_id, user=request.user)  # Ensure the log belongs to the user
        log.delete()
        return JsonResponse({'success': True})
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
        'projects': projects,
        'clients': clients,
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


# @login_required
# def edit_project(request, project_id):
#     project = get_object_or_404(Project, id=project_id)
#     contracts = project.contract.all()
#     clients = Client.objects.all()
#     users = User.objects.all()
#     contract_form = ContractForm()

#     if request.method == 'POST':
#         print("POST data received:", request.POST)  # Debugging line

#         if 'project_name' in request.POST:
#             form = ProjectForm(request.POST, instance=project)
#             if form.is_valid():
#                 form.save()
#                 print("Project form saved successfully")  # Debugging line
#                 return redirect('projects')
#             else:
#                 print("Project form errors:", form.errors)  # Debugging line

#         elif 'contract_name' in request.POST and not request.POST.get('contract_id'):
#             contract_name = request.POST.get('contract_name')
#             user_ids = request.POST.getlist('users')
#             section_names = request.POST.getlist('section_name')
#             item_names = request.POST.getlist('item_name')
#             task_names = request.POST.getlist('task_name')

#             contract = Contract.objects.create(contract_name=contract_name)
#             contract.user.set(user_ids)

#             created_tasks = {}
#             created_items = {}
#             created_sections = {}

#             for section_name in section_names:
#                 section, created = Section.objects.get_or_create(section_name=section_name)
#                 created_sections[section_name] = section

#                 for item_name in item_names:
#                     item, created = Item.objects.get_or_create(Item_name=item_name)
#                     created_items[item_name] = item

#                     for task_name in task_names:
#                         task, created = Task.objects.get_or_create(task_name=task_name)
#                         created_tasks[task_name] = task
#                         item.tasks.add(task)

#                     section.Item.add(item)
#                 contract.section.add(section)

#             contract.save()
#             project.contract.add(contract)
#             project.save()
#             return redirect('edit_project', project_id=project.id)

#         elif request.POST.get('contract_id'):
#             contract_id = request.POST['contract_id']
#             contract = get_object_or_404(Contract, id=contract_id)
#             contract_form = ContractForm(request.POST, instance=contract)
#             if contract_form.is_valid():
#                 contract_form.save()
#                 print("Contract form updated successfully")  # Debugging line
#                 return redirect('edit_project', project_id=project.id)
#             else:
#                 print("Contract form errors:", contract_form.errors)  # Debugging line
#         else:
#             form = ProjectForm(instance=project)
#     else:
#         form = ProjectForm(instance=project)

#     context = {
#         'form': form,
#         'project': project,
#         'contracts': contracts,
#         'contract_form': contract_form,
#         'clients': clients,
#         'users': users,
#     }
#     return render(request, 'tracker/edit_project.html', context)


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    contracts = project.contract.all()
    clients = Client.objects.all()
    users = User.objects.all()
    contract_form = ContractForm()
    section_library = SectionLibrary.objects.all()

    if request.method == 'POST':
        if 'project_name' in request.POST:
            return handle_project_form(request, project)
        elif 'contract_name' in request.POST and not request.POST.get('contract_id'):
            return handle_new_contract_form(request, project)
        elif request.POST.get('contract_id'):
            return handle_existing_contract_form(request, project)
    else:
        form = ProjectForm(instance=project)

    context = {
        'form': form,
        'project': project,
        'contracts': contracts,
        'contract_form': contract_form,
        'clients': clients,
        'users': users,
        'section_library': section_library,
    }
    return render(request, 'tracker/edit_project.html', context)


def get_library_section(request, section_id):
    section = get_object_or_404(SectionLibrary, id=section_id)
    items = section.items.all()
    section_data = {
        'section_name': section.name,
        'items': [
            {
                'item_name': item.name,
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


def handle_existing_contract_form(request, project):
    contract_id = request.POST['contract_id']
    contract = get_object_or_404(Contract, id=contract_id)
    
    contract_data = request.POST.copy()
    user_ids = request.POST.getlist('users')
    contract_data.setlist('user', user_ids)

    contract_form = ContractForm(contract_data, instance=contract)

    if contract_form.is_valid():
        contract_form.save()
        contract_json = request.POST.get('contract_json')
        
        print("Received contract JSON:", contract_json)  # Debugging line

        if contract_json:
            try:
                contract_data = json.loads(contract_json)

                # Handle section updates and additions
                for section_data in contract_data['sections']:
                    section_name = section_data['section_name']
                    section, created = Section.objects.get_or_create(section_name=section_name)

                    for item_data in section_data['items']:
                        item_name = item_data['item_name']
                        item, created = Item.objects.get_or_create(Item_name=item_name)

                        item.tasks.clear()  # Clear existing tasks before updating
                        for task_data in item_data['tasks']:
                            task_name = task_data['task_name']
                            task, created = Task.objects.get_or_create(task_name=task_name)
                            item.tasks.add(task)

                        section.Item.add(item)

                    contract.section.add(section)

                contract.save()
                project.contract.add(contract)
                project.save()

                messages.success(request, "Contract updated successfully.")
            except json.JSONDecodeError:
                messages.error(request, "Error decoding the contract JSON data.")
        else:
            messages.error(request, "No contract JSON data provided.")
    else:
        print("Contract form errors:", contract_form.errors)  # Debugging line
        messages.error(request, "Error updating contract: {}".format(contract_form.errors))

    return redirect('edit_project', project_id=project.id)

def handle_new_contract_form(request, project):
    contract_name = request.POST.get('contract_name')
    user_ids = request.POST.getlist('users')

    # Debugging print statement
    print("POST data:", request.POST)

    contract = Contract.objects.create(contract_name=contract_name)
    contract.user.set(user_ids)

    contract_json = request.POST.get('contract_json')
    
    print("Received contract JSON:", contract_json)  # Debugging line

    if contract_json:
        try:
            contract_data = json.loads(contract_json)
            
            for section_data in contract_data['sections']:
                section_name = section_data['section_name']
                section, created = Section.objects.update_or_create(
                    section_name=section_name,
                    defaults={'section_name': section_name}
                )
                print("Processed section:", section_name)  # Debugging line

                for item_data in section_data['items']:
                    item_name = item_data['item_name']
                    item, created = Item.objects.update_or_create(
                        Item_name=item_name,
                        defaults={'Item_name': item_name}
                    )
                    print("Processed item:", item_name)  # Debugging line

                    for task_data in item_data['tasks']:
                        task_name = task_data['task_name']
                        task, created = Task.objects.update_or_create(
                            task_name=task_name,
                            defaults={'task_name': task_name}
                        )
                        print("Processed task:", task_name)  # Debugging line
                        item.tasks.add(task)

                    section.Item.add(item)

                contract.section.add(section)

            contract.save()
            project.contract.add(contract)
            project.save()

            messages.success(request, "New contract added successfully.")
        except json.JSONDecodeError:
            messages.error(request, "Error decoding the contract JSON data.")
    else:
        messages.error(request, "No contract JSON data provided.")

    return redirect('edit_project', project_id=project.id)





def update_contract_details(request, contract):
    section_names = request.POST.getlist('section_name')
    item_names = request.POST.getlist('item_name')
    task_names = request.POST.getlist('task_name')

    contract.section.clear()
    for section_name in section_names:
        section, _ = Section.objects.get_or_create(section_name=section_name)
        section.Item.clear()
        for item_name in item_names:
            item, _ = Item.objects.get_or_create(Item_name=item_name)
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
            return redirect('projects')
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
        log_contract_name = form.cleaned_data['log_contract']
        log_tasks = form.cleaned_data['log_tasks']
        log_section = form.cleaned_data['log_section']
        log_Item = form.cleaned_data['log_Item']
        log_time = form.cleaned_data['log_time']
        log_timestamps = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S')
        
        log_project = get_object_or_404(Project, project_name=log_project_name)
        log_contract = get_object_or_404(Contract, contract_name=log_contract_name)
        log_section = get_object_or_404(Section, section_name=log_section)
        log_Item = get_object_or_404(Item, Item_name=log_Item)

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

#Main view to create log
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
        log_Item = form.cleaned_data['log_Item']
        log_time = form.cleaned_data['log_time']
        log_timestamps = timezone.now().astimezone(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S')

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
        'projects': projects,
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
        project_address = request.POST.get('project_address')
        new_project = Project.objects.create(
            user=request.user,
            project_name=project_name,
            project_address=project_address,
            project_no="PN-" + str(Project.objects.count() + 1)  # Example project number
        )
        return redirect('project_details')
    return redirect('project_details')


def load_contract_data(request):
    contract_id = request.GET.get('contract_id')
    contract = get_object_or_404(Contract, id=contract_id)

    users = list(User.objects.all().values('id', 'username'))
    sections = contract.section.all()
    section_data = []

    for section in sections:
        items = section.Item.all()
        item_data = [{
            'id': item.id, 
            'Item_name': item.Item_name,
            'budget': item.budget,  # Ensure budget is included here
            'users': list(item.users.values_list('id', flat=True)),  # Get user IDs for the item
            'tasks': list(item.tasks.values('id', 'task_name'))  # Include tasks for each item
        } for item in items]
        section_data.append({
            'section_name': section.section_name,
            'items': item_data
        })

    contract_data = {
        'contract_name': contract.contract_name,
        'users': users,
        'sections': section_data
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

def check_item_name(request):
    item_name = request.GET.get('item_name', None)
    is_taken = Item.objects.filter(Item_name__iexact=item_name).exists()
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

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def add_budget(request):
    if request.method == 'POST':
        print(request.POST)  # Debugging line
        contract_id = request.POST.get('contract_id')
        if not contract_id:
            return JsonResponse({'error': 'Missing contract ID'}, status=400)

        contract = get_object_or_404(Contract, id=contract_id)

        for section in contract.section.all():
            for item in section.Item.all():
                budget_key = f'budget_{item.id}'
                if budget_key in request.POST:
                    try:
                        print(f"Updating item {item.id} with budget {request.POST[budget_key]}")  # Debugging line
                        item.budget = request.POST[budget_key]
                        item.save()
                    except Item.DoesNotExist:
                        continue

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

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
