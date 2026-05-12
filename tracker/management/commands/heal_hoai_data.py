"""
Heal contracts whose hoai_data was corrupted by a no-change save through the
contract form modal (display spans serialized as "-" placeholders, overwriting
valid interpolation / grundhonorar values).

For every Contract whose hoai_data contains "-" / "" / None in the
interpolation, grundhonorar, interpolated_basishonorarsatz,
interpolated_oberer_honorarsatz, or zuschlag_amount fields, this command
recomputes the values from the still-valid inputs (serviceProfile,
anrechenbareKosten, honorarzone, honorarsatz, zuschlag) using the same Excel
table lookup HOAICalculationView uses, and writes the result back.

Usage:
    python manage.py heal_hoai_data              # dry run
    python manage.py heal_hoai_data --apply      # commit
    python manage.py heal_hoai_data --apply --contract-ids 351 412
"""

import os

import pandas as pd
from babel.numbers import format_decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from tracker.models import Contract, ServiceProfile


PLACEHOLDER_VALUES = {"", "-", "-€", "0,00", None}
INTERPOLATION_KEYS = (
    "lower_bound_cost",
    "upper_bound_cost",
    "lower_bound_von",
    "upper_bound_von",
    "lower_bound_bis",
    "upper_bound_bis",
)


def _is_placeholder(value):
    if value is None:
        return True
    return str(value).strip() in {"", "-", "-€"}


def _fmt_de(value):
    return format_decimal(float(value), format="#,##0.00", locale="de_DE")


def _parse_numeric(value):
    """Accept a string that may be German-formatted, plain decimal, or a number."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s in {"-", "-€"}:
        return None
    # German format: "1.234,56" -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _resolve_excel_path(profile):
    """Mirror HOAICalculationView's fallback: MEDIA_ROOT first, then BASE_DIR/hoai_tables/."""
    try:
        primary = profile.excel_file.path
    except (ValueError, AttributeError):
        primary = None
    if primary and os.path.exists(primary):
        return primary
    if profile.excel_file and profile.excel_file.name:
        fallback = os.path.join(
            settings.BASE_DIR, "hoai_tables", os.path.basename(profile.excel_file.name)
        )
        if os.path.exists(fallback):
            return fallback
    return None


SATZ_FACTOR = {
    "Basishonorarsatz": 0.0,
    "Viertelsatz": 0.25,
    "Mittelsatz": 0.50,
    "Dreiviertelsatz": 0.75,
    "Oberer Honorarsatz": 1.00,
}


def _recompute_hoai(hoai_data):
    """
    Recompute interpolation, grundhonorar, zuschlag_amount from the still-valid
    inputs. Returns (new_hoai_data, error_message). new_hoai_data is None on error.
    """
    profile_id = hoai_data.get("serviceProfile")
    cost_input = _parse_numeric(hoai_data.get("anrechenbareKosten"))
    fee_zone = hoai_data.get("honorarzone")
    honorarsatz = hoai_data.get("honorarsatz") or "Mittelsatz"
    zuschlag_pct = _parse_numeric(hoai_data.get("zuschlag")) or 0.0

    if not profile_id:
        return None, "missing serviceProfile"
    if cost_input is None:
        return None, "missing/invalid anrechenbareKosten"
    if not fee_zone:
        return None, "missing honorarzone"
    if honorarsatz not in SATZ_FACTOR:
        return None, f"unknown honorarsatz '{honorarsatz}'"

    try:
        profile = ServiceProfile.objects.get(id=profile_id)
    except ServiceProfile.DoesNotExist:
        return None, f"ServiceProfile {profile_id} not found"

    excel_path = _resolve_excel_path(profile)
    if not excel_path:
        return None, f"Excel file for profile '{profile.name}' not found on disk"

    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        return None, f"pd.read_excel failed: {type(e).__name__}: {e}"

    cost_col = "Anrechenbare Kosten (€)"
    von_col = f"Honorarzone {fee_zone} (von)"
    bis_col = f"Honorarzone {fee_zone} (bis)"
    for col in (cost_col, von_col, bis_col):
        if col not in df.columns:
            return None, f"column '{col}' missing from Excel"

    lower_rows = df[df[cost_col] <= cost_input]
    upper_rows = df[df[cost_col] > cost_input]
    if lower_rows.empty or upper_rows.empty:
        return None, f"anrechenbareKosten={cost_input} outside Excel range"

    lower = lower_rows.iloc[-1]
    upper = upper_rows.iloc[0]

    a, aa = float(lower[cost_col]), float(upper[cost_col])
    b, bb = float(lower[von_col]), float(upper[von_col])
    c, cc = float(lower[bis_col]), float(upper[bis_col])

    if aa == a:
        return None, "degenerate interval (aa == a) in Excel"

    honor_from = b + ((cost_input - a) * (bb - b) / (aa - a))
    honor_to = c + ((cost_input - a) * (cc - c) / (aa - a))

    factor = SATZ_FACTOR[honorarsatz]
    net_honor = honor_from + (honor_to - honor_from) * factor
    zuschlag_amount = (net_honor * zuschlag_pct) / 100.0
    grundhonorar = net_honor + zuschlag_amount

    new_data = dict(hoai_data)
    new_data["interpolation"] = {
        "lower_bound_cost": _fmt_de(a),
        "upper_bound_cost": _fmt_de(aa),
        "lower_bound_von": _fmt_de(b),
        "upper_bound_von": _fmt_de(bb),
        "lower_bound_bis": _fmt_de(c),
        "upper_bound_bis": _fmt_de(cc),
    }
    new_data["interpolated_basishonorarsatz"] = _fmt_de(honor_from)
    new_data["interpolated_oberer_honorarsatz"] = _fmt_de(honor_to)
    new_data["zuschlag_amount"] = _fmt_de(zuschlag_amount)
    new_data["grundhonorar"] = _fmt_de(grundhonorar)
    new_data["honorarsatz_factor"] = int(factor * 100)
    return new_data, None


def _contract_needs_heal(hoai_data):
    if not hoai_data:
        return False
    if _is_placeholder(hoai_data.get("grundhonorar")):
        return True
    if _is_placeholder(hoai_data.get("interpolated_basishonorarsatz")):
        return True
    if _is_placeholder(hoai_data.get("interpolated_oberer_honorarsatz")):
        return True
    if _is_placeholder(hoai_data.get("zuschlag_amount")):
        return True
    interp = hoai_data.get("interpolation") or {}
    if not interp:
        return True
    for k in INTERPOLATION_KEYS:
        if _is_placeholder(interp.get(k)):
            return True
    return False


class Command(BaseCommand):
    help = (
        "Find contracts whose hoai_data has '-' placeholder values (from a "
        "no-change save through the corrupted modal) and recompute the missing "
        "fields from the still-valid inputs. Dry-run by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist the changes. Without this flag the command only reports what would change.",
        )
        parser.add_argument(
            "--contract-ids",
            nargs="+",
            type=int,
            help="Limit to specific Contract IDs.",
        )

    def handle(self, *args, **opts):
        apply = opts["apply"]
        ids = opts.get("contract_ids")

        qs = Contract.objects.exclude(hoai_data=None).exclude(hoai_data={})
        if ids:
            qs = qs.filter(id__in=ids)

        total = qs.count()
        needs_heal = []
        healed = []
        skipped = []

        for contract in qs:
            hoai_data = contract.hoai_data or {}
            if not _contract_needs_heal(hoai_data):
                continue
            needs_heal.append(contract.id)

            new_data, err = _recompute_hoai(hoai_data)
            if err:
                skipped.append((contract.id, contract.contract_no, contract.contract_name, err))
                self.stdout.write(self.style.WARNING(
                    f"  SKIP contract {contract.id} ({contract.contract_no} - {contract.contract_name}): {err}"
                ))
                continue

            old_gh = hoai_data.get("grundhonorar")
            new_gh = new_data["grundhonorar"]
            self.stdout.write(self.style.SUCCESS(
                f"  HEAL contract {contract.id} ({contract.contract_no} - {contract.contract_name}): "
                f"grundhonorar {old_gh!r} -> {new_gh!r}"
            ))

            if apply:
                with transaction.atomic():
                    contract.hoai_data = new_data
                    contract.save(update_fields=["hoai_data"])
            healed.append(contract.id)

        self.stdout.write("")
        self.stdout.write(f"Scanned {total} contract(s) with hoai_data.")
        self.stdout.write(f"  Needed healing: {len(needs_heal)}")
        self.stdout.write(f"  Recomputed:     {len(healed)}")
        self.stdout.write(f"  Skipped:        {len(skipped)}")
        if not apply and healed:
            self.stdout.write(self.style.WARNING(
                "\nDry run — re-run with --apply to persist the changes."
            ))
