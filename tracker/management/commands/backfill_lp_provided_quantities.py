from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import re

LP_REGEX = re.compile(r'\bLP\s*([1-9])\b', flags=re.IGNORECASE)


class Command(BaseCommand):
    help = (
        "Dry-run (default) or apply a backfill that ensures all enabled HOAI LP items "
        "exist in each invoice's provided_quantities with quantity=0, preserving existing entries."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the changes (default is a dry-run).",
        )
        parser.add_argument(
            "--contract-ids",
            nargs="+",
            type=int,
            help="Limit to specific Contract IDs.",
        )
        parser.add_argument(
            "--invoice-ids",
            nargs="+",
            type=int,
            help="Limit to specific Invoice IDs.",
        )
        parser.add_argument(
            "--sample",
            type=int,
            default=5,
            help="Show up to N invoice diffs (default: 5).",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Minimal output (suppresses per-invoice diffs).",
        )

    def handle(self, *args, **opts):
        from tracker.models import Contract, Invoice, Section, Item  # import inside for app readiness

        apply = opts["apply"]
        sample = max(0, int(opts["sample"] or 0))
        quiet = bool(opts["quiet"])
        contract_ids = opts.get("contract_ids") or []
        invoice_ids = opts.get("invoice_ids") or []

        # Base queryset: HOAI contracts only
        contracts_qs = Contract.objects.exclude(hoai_data=None)
        if contract_ids:
            contracts_qs = contracts_qs.filter(id__in=contract_ids)

        total_contracts = 0
        total_invoices_seen = 0
        total_invoices_changed = 0
        total_keys_added = 0
        sample_shown = 0

        if apply:
            self.stdout.write(self.style.WARNING("Applying changes (no longer a dry-run)."))
        else:
            self.stdout.write(self.style.WARNING("Dry-run: no changes will be written."))

        for contract in contracts_qs.iterator():
            hoai = contract.hoai_data or {}
            if not hoai:
                continue

            is_hoai = hoai.get("is_hoai_contract")
            if not is_hoai:
                continue

            lp_enabled = hoai.get("lp_enabled") or {}
            if not isinstance(lp_enabled, dict):
                continue

            total_contracts += 1

            # Collect LP sections (enabled only)
            lp_sections = []
            for s in contract.section.all():
                name = (s.section_name or "").strip()
                m = LP_REGEX.search(name)
                if not m:
                    continue
                lp_no = m.group(1)  # '1'..'9'
                if lp_enabled.get(f"lp{lp_no}", False):
                    lp_sections.append((s, lp_no))

            if not lp_sections:
                continue

            # Build item_id -> rate map for these LP sections
            lp_item_rate = {}
            for section, _lp_no in lp_sections:
                # NOTE: Section.Item is the M2M field in your models
                for item in section.Item.all().only("id", "rate"):
                    key = str(item.id)
                    rate_val = item.rate
                    try:
                        rate_float = float(rate_val) if rate_val is not None else 0.0
                    except Exception:
                        try:
                            rate_float = float(Decimal(str(rate_val)))
                        except Exception:
                            rate_float = 0.0
                    lp_item_rate[key] = rate_float

            if not lp_item_rate:
                continue

            inv_qs = Invoice.objects.filter(contract=contract)
            if invoice_ids:
                inv_qs = inv_qs.filter(id__in=invoice_ids)

            for inv in inv_qs.iterator():
                total_invoices_seen += 1

                pq = inv.provided_quantities or {}
                if not isinstance(pq, dict):
                    pq = {}

                missing = {k: v for k, v in lp_item_rate.items() if k not in pq}
                if not missing:
                    continue

                # Prepare new JSON with missing LP items at quantity 0
                new_pq = dict(pq)
                for k, rate_float in missing.items():
                    new_pq[k] = {"rate": rate_float, "quantity": 0}

                if not quiet and sample_shown < sample:
                    self.stdout.write(f"\nInvoice id={inv.id} title={inv.title!r}")
                    self.stdout.write("  Missing LP item keys to be added (quantity=0):")
                    self.stdout.write("   " + ", ".join(sorted(missing.keys())))

                total_invoices_changed += 1
                total_keys_added += len(missing)
                sample_shown += 1

                if apply:
                    # Avoid calling inv.save() to not trigger custom save logic
                    Invoice.objects.filter(pk=inv.pk).update(provided_quantities=new_pq)

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Summary ==="))
        self.stdout.write(f"HOAI contracts processed: {total_contracts}")
        self.stdout.write(f"Invoices scanned:         {total_invoices_seen}")
        self.stdout.write(f"Invoices changed:         {total_invoices_changed}")
        self.stdout.write(f"LP item keys added:       {total_keys_added}")

        if not apply:
            self.stdout.write(self.style.WARNING("\nDry-run only. Use --apply to write changes."))
