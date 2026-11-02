"""
External API views for the BCK Tracker app.

Currently exposes:
    GET /api/hours/   — daily hours per employee for a date range
"""
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .api_auth import APIKeyAuthentication, HasAPIKey

User = get_user_model()


class EmployeeHoursView(APIView):
    """
    Returns the total logged hours per calendar day for one employee.

    Authentication: Api-Key header  (Authorization: Api-Key <key>)
    Permission:     Any request that passes authentication is allowed.

    Query parameters
    ----------------
    username  str          Django username of the employee (required)
    from      YYYY-MM-DD   Start date, inclusive (required)
    to        YYYY-MM-DD   End date, inclusive (required)

    Response — 200 OK
    ------------------
    [
      {"date": "2026-04-01", "hours": 7.5},
      {"date": "2026-04-02", "hours": 8.0},
      ...
    ]

    Only dates that have at least one log entry are returned.
    Dates within the range with no logs are omitted (not returned as 0).

    Error responses
    ---------------
    400  Missing or invalid query parameters
    401  Missing or invalid API key
    404  Username not found
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def get(self, request):
        # ── 1. Validate query parameters ────────────────────────────────────
        username = request.query_params.get('username', '').strip()
        from_str = request.query_params.get('from', '').strip()
        to_str   = request.query_params.get('to', '').strip()

        errors = {}
        if not username:
            errors['username'] = 'This parameter is required.'
        if not from_str:
            errors['from'] = 'This parameter is required.'
        if not to_str:
            errors['to'] = 'This parameter is required.'

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from_date = datetime.strptime(from_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'errors': {'from': 'Must be in YYYY-MM-DD format.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            to_date = datetime.strptime(to_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'errors': {'to': 'Must be in YYYY-MM-DD format.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if to_date < from_date:
            return Response(
                {'errors': {'to': "'to' must be on or after 'from'."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (to_date - from_date).days > 366:
            return Response(
                {'errors': {'range': 'Date range cannot exceed 366 days.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 2. Look up employee ──────────────────────────────────────────────
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': f"No employee found with username '{username}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── 3. Query logs ────────────────────────────────────────────────────
        # log_timestamps is a CharField storing "YYYY-MM-DD HH:MM:SS" (Europe/Berlin).
        # Lexicographic comparison works correctly for ISO-format date strings.
        from_bound = from_date.strftime('%Y-%m-%d')
        to_bound   = (to_date + timedelta(days=1)).strftime('%Y-%m-%d')  # exclusive upper bound

        from .models import Logs
        logs = (
            Logs.objects
            .filter(
                user=user,
                log_timestamps__gte=from_bound,
                log_timestamps__lt=to_bound,
            )
            .values('log_timestamps', 'log_time')
        )

        # ── 4. Aggregate by date ─────────────────────────────────────────────
        hours_by_date = defaultdict(float)
        for log in logs:
            date_str = log['log_timestamps'][:10]  # "YYYY-MM-DD HH:MM:SS" → "YYYY-MM-DD"
            hours_by_date[date_str] += log['log_time']

        # ── 5. Return sorted result ──────────────────────────────────────────
        result = [
            {'date': date, 'hours': round(hours, 4)}
            for date, hours in sorted(hours_by_date.items())
        ]

        return Response(result, status=status.HTTP_200_OK)


class EmployeeProjectsView(APIView):
    """
    GET /api/projects/  — projects an employee is assigned to, plus their saved
    per-project logging preset (default contract/section/item/task) where one
    exists.

    An external helper maps the firm's project codes (``project_no``, e.g.
    "26-004") to loggable projects and uses ``has_preset`` to know which ones it
    can create a log for with no extra ids.

    Auth: Api-Key header.
    Query params:
        username  str   (required)  Django username
        active    0|1   (optional, default 1 → only status "InBearbeitung")
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def get(self, request):
        username = request.query_params.get('username', '').strip()
        if not username:
            return Response(
                {'errors': {'username': 'This parameter is required.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        active = request.query_params.get('active', '1').strip()

        from .models import Project, ProjectPreset

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': f"No employee found with username '{username}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        projects = Project.objects.filter(user=user)
        if active == '1':
            projects = projects.filter(status='0')

        presets = {
            pr.project_id: pr
            for pr in ProjectPreset.objects
            .filter(user=user)
            .select_related('default_contract', 'default_section', 'default_Item', 'default_task')
        }

        out = []
        for p in projects.order_by('project_no'):
            pr = presets.get(p.id)
            preset = None
            if pr and pr.default_contract_id and pr.default_section_id and pr.default_Item_id:
                preset = {
                    'contract_id': pr.default_contract_id,
                    'contract': str(pr.default_contract) if pr.default_contract else None,
                    'section_id': pr.default_section_id,
                    'section': pr.default_section.section_name if pr.default_section else None,
                    'item_id': pr.default_Item_id,
                    'item': pr.default_Item.Item_name if pr.default_Item else None,
                    'task': pr.default_task.task_name if pr.default_task else None,
                }
            out.append({
                'project_id': p.id,
                'project_no': p.project_no,
                'project_name': p.project_name,
                'status': p.get_status_display(),
                'has_preset': preset is not None,
                'preset': preset,
            })

        return Response(out, status=status.HTTP_200_OK)


class CreateLogView(APIView):
    """
    POST /api/logs/  — create a single time-log entry for an employee.

    Contract/section/item are taken from the employee's saved ProjectPreset for
    the project unless explicit ids are supplied. If the employee has no preset
    for that project and no ids are given, returns 400 with ``needs_preset``.

    Auth: Api-Key header.
    JSON body:
        username     str         (required)  Django username
        project      str         (required)  project_no OR project_name
        hours        number      (required)  > 0 and ≤ 24
        date         YYYY-MM-DD   (optional, default: today Europe/Berlin)
        task         str         (optional)  free-text task note
        contract_id  int         (optional)  explicit override …
        section_id   int         (optional)  … all three must be given together
        item_id      int         (optional)

    Success — 201 Created: the created log summary.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def post(self, request):
        import pytz
        from django.utils import timezone as djtz
        from django.db.models import Q
        from .models import Project, ProjectPreset, Contract, Section, Item, Logs

        data = request.data if isinstance(request.data, dict) else {}
        username = str(data.get('username', '')).strip()
        project_ref = str(data.get('project', '')).strip()
        hours_raw = data.get('hours', None)
        date_str = str(data.get('date', '')).strip()
        task = str(data.get('task', '')).strip() or None

        errors = {}
        if not username:
            errors['username'] = 'This field is required.'
        if not project_ref:
            errors['project'] = 'This field is required.'
        if hours_raw is None or hours_raw == '':
            errors['hours'] = 'This field is required.'
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            hours = round(float(hours_raw), 4)
        except (TypeError, ValueError):
            return Response({'errors': {'hours': 'Must be a number.'}}, status=status.HTTP_400_BAD_REQUEST)
        if hours <= 0 or hours > 24:
            return Response(
                {'errors': {'hours': 'Must be greater than 0 and at most 24.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        berlin = pytz.timezone('Europe/Berlin')
        now_berlin = djtz.now().astimezone(berlin)
        if date_str:
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'errors': {'date': 'Must be in YYYY-MM-DD format.'}}, status=status.HTTP_400_BAD_REQUEST)
            if d > now_berlin.date():
                return Response({'errors': {'date': 'Date cannot be in the future.'}}, status=status.HTTP_400_BAD_REQUEST)
            if (now_berlin.date() - d).days > 60:
                return Response({'errors': {'date': 'Date is too far in the past (max 60 days).'}}, status=status.HTTP_400_BAD_REQUEST)
        else:
            d = now_berlin.date()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': f"No employee found with username '{username}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Resolve the project (by project_no or project_name); must belong to the user.
        proj_qs = (
            Project.objects
            .filter(user=user)
            .filter(Q(project_no=project_ref) | Q(project_name__iexact=project_ref))
        )
        # Prefer an active project if the number matches several.
        project = proj_qs.filter(status='0').first() or proj_qs.first()
        if not project:
            return Response(
                {'error': f"No project '{project_ref}' assigned to '{username}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Resolve contract/section/item — explicit ids, else the user's preset.
        cid = data.get('contract_id')
        sid = data.get('section_id')
        iid = data.get('item_id')
        if cid or sid or iid:
            if not (cid and sid and iid):
                return Response(
                    {'errors': {'ids': 'Provide contract_id, section_id AND item_id together, or none (to use your saved preset).'}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            contract = Contract.objects.filter(id=cid).first()
            section = Section.objects.filter(id=sid).first()
            item = Item.objects.filter(id=iid).first()
            if not (contract and section and item):
                return Response(
                    {'errors': {'ids': 'One of contract_id/section_id/item_id does not exist.'}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            preset = ProjectPreset.objects.filter(user=user, project=project).first()
            if not preset or not (preset.default_contract_id and preset.default_section_id and preset.default_Item_id):
                return Response(
                    {
                        'error': (
                            f"No logging preset set for project "
                            f"'{project.project_no}-{project.project_name}'. Set your default "
                            f"contract/section/item once in the Tracker app, or pass "
                            f"contract_id/section_id/item_id."
                        ),
                        'needs_preset': True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            contract = preset.default_contract
            section = preset.default_section
            item = preset.default_Item
            if task is None and preset.default_task:
                task = preset.default_task.task_name

        log_timestamps = f"{d.strftime('%Y-%m-%d')} {now_berlin.strftime('%H:%M:%S')}"
        log = Logs.objects.create(
            user=user,
            log_project_name=project.project_name,
            log_contract=contract,
            log_section=section,
            log_Item=item,
            log_time=hours,
            log_timestamps=log_timestamps,
            log_tasks=task,
        )

        return Response(
            {
                'id': log.id,
                'username': user.username,
                'project': f"{project.project_no}-{project.project_name}",
                'date': d.strftime('%Y-%m-%d'),
                'hours': hours,
                'contract': str(contract),
                'section': section.section_name,
                'item': item.Item_name,
                'task': task,
            },
            status=status.HTTP_201_CREATED,
        )
