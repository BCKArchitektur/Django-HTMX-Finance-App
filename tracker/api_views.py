"""
External API views for the BCK Tracker app.

Currently exposes:
    GET /api/hours/   — daily hours per employee for a date range
"""
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .api_auth import APIKeyAuthentication

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
    permission_classes = [IsAuthenticated]

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
