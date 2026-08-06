"""
Batch re-home a set of Logs from one project/contract/section/item to another.

Built for the case where time was logged against the generic
"Büro / Allgemein / Allgemein / Allgemein" bucket but actually belongs to a real
project contract (e.g. BRMHQS Burmester / Zusätzliche Leistungen /
Stundennachweis).

log_project_name is a plain CharField, but log_contract, log_section and
log_Item are ForeignKeys — so the destination Contract/Section/Item objects must
already exist and be wired into the destination Project hierarchy
(Project.contract -> Contract.section -> Section.Item). This command resolves
them through that hierarchy and refuses to guess.

user, log_time, log_timestamps and log_tasks are never touched.

Usage:
    # 1. See what the destination hierarchy actually looks like
    python manage.py rehome_logs --inspect

    # 2. Dry run — lists every log that would change
    python manage.py rehome_logs

    # 3. Commit
    python manage.py rehome_logs --apply

    # Narrow / widen the selection
    python manage.py rehome_logs --task-contains BURM --user TN
    python manage.py rehome_logs --log-ids 1204 1205 1206 --apply

    # One log gets a different item than the rest
    python manage.py rehome_logs --item-for 1204=Bauzeichner/in --apply
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracker.models import Contract, Item, Logs, Project, Section


# Destination defaults are baked in rather than passed as CLI args: umlauts
# survive a code deploy reliably, but not always a `heroku run` argv round trip.
DEST_PROJECT = "BRMHQS Burmester"
DEST_CONTRACT = "Zusätzliche Leistungen"
DEST_SECTION = "Stundennachweis"
DEST_ITEM = "Allgemein"

SRC_PROJECT = "Büro"
SRC_TASK_CONTAINS = "BURM"


class Command(BaseCommand):
    help = "Batch re-home Logs to a different project / contract / section / item."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Commit the changes. Without this the command is a dry run.",
        )
        parser.add_argument(
            "--inspect",
            action="store_true",
            help="Print the destination project hierarchy and exit. Run this first.",
        )
        parser.add_argument(
            "--log-ids",
            nargs="+",
            type=int,
            help="Explicit Logs primary keys. Overrides the name/task filters.",
        )
        parser.add_argument(
            "--source-project",
            default=SRC_PROJECT,
            help=f'Match logs whose log_project_name equals this (default: "{SRC_PROJECT}").',
        )
        parser.add_argument(
            "--task-contains",
            default=SRC_TASK_CONTAINS,
            help=f'Match logs whose log_tasks contains this (default: "{SRC_TASK_CONTAINS}"). '
            'Pass "" to disable.',
        )
        parser.add_argument(
            "--user",
            help="Optional: also require this username.",
        )
        parser.add_argument(
            "--project",
            default=DEST_PROJECT,
            help=f'Destination project name (default: "{DEST_PROJECT}").',
        )
        parser.add_argument(
            "--contract",
            default=DEST_CONTRACT,
            help=f'Destination contract name (default: "{DEST_CONTRACT}").',
        )
        parser.add_argument(
            "--section",
            default=DEST_SECTION,
            help=f'Destination section name (default: "{DEST_SECTION}").',
        )
        parser.add_argument(
            "--item",
            default=DEST_ITEM,
            help=f'Destination item name for all logs (default: "{DEST_ITEM}").',
        )
        parser.add_argument(
            "--item-for",
            nargs="+",
            default=[],
            metavar="LOG_ID=ITEM_NAME",
            help="Per-log item override, e.g. --item-for 1204=Bauzeichner/in",
        )

    # ---------------------------------------------------------------- helpers

    def _resolve_project(self, name):
        projects = list(Project.objects.filter(project_name__iexact=name))
        if not projects:
            projects = list(Project.objects.filter(project_name__icontains=name))
        if not projects:
            available = ", ".join(
                Project.objects.values_list("project_name", flat=True).order_by("project_name")[:40]
            )
            raise CommandError(f'No project matches "{name}". Projects: {available}')
        if len(projects) > 1:
            found = ", ".join(f"{p.project_no}-{p.project_name}" for p in projects)
            raise CommandError(f'"{name}" is ambiguous — matches: {found}')
        return projects[0]

    def _resolve_contract(self, project, name):
        contracts = list(project.contract.filter(contract_name__iexact=name))
        if not contracts:
            available = ", ".join(project.contract.values_list("contract_name", flat=True))
            raise CommandError(
                f'Project "{project.project_name}" has no contract "{name}". '
                f"Contracts: {available or '(none)'}"
            )
        if len(contracts) > 1:
            found = ", ".join(f"id={c.id} no={c.contract_no}" for c in contracts)
            raise CommandError(f'Contract "{name}" is ambiguous under this project — {found}')
        return contracts[0]

    def _resolve_section(self, contract, name):
        sections = list(contract.section.filter(section_name__iexact=name))
        if not sections:
            available = ", ".join(contract.section.values_list("section_name", flat=True))
            raise CommandError(
                f'Contract "{contract.contract_name}" has no section "{name}". '
                f"Sections: {available or '(none)'}"
            )
        if len(sections) > 1:
            found = ", ".join(f"id={s.id}" for s in sections)
            raise CommandError(f'Section "{name}" is ambiguous under this contract — {found}')
        return sections[0]

    def _resolve_item(self, section, name):
        items = list(section.Item.filter(Item_name__iexact=name))
        if not items:
            available = ", ".join(section.Item.values_list("Item_name", flat=True))
            raise CommandError(
                f'Section "{section.section_name}" has no item "{name}". '
                f"Items: {available or '(none)'}"
            )
        if len(items) > 1:
            found = ", ".join(f"id={i.id}" for i in items)
            raise CommandError(f'Item "{name}" is ambiguous under this section — {found}')
        return items[0]

    def _inspect(self, project_name):
        project = self._resolve_project(project_name)
        self.stdout.write(self.style.MIGRATE_HEADING(f"{project.project_no} — {project.project_name}"))
        for contract in project.contract.all().order_by("contract_name"):
            self.stdout.write(f"  Contract  {contract.contract_name}  (id={contract.id}, no={contract.contract_no})")
            for section in contract.section.all().order_by("order", "section_name"):
                self.stdout.write(f"    Section  {section.section_name}  (id={section.id})")
                for item in section.Item.all().order_by("order", "Item_name"):
                    self.stdout.write(
                        f"      Item   {item.Item_name}  (id={item.id}, unit={item.unit}, rate={item.rate})"
                    )

    def _parse_item_overrides(self, raw):
        overrides = {}
        for entry in raw:
            if "=" not in entry:
                raise CommandError(f'--item-for expects LOG_ID=ITEM_NAME, got "{entry}"')
            log_id, item_name = entry.split("=", 1)
            try:
                overrides[int(log_id.strip())] = item_name.strip()
            except ValueError:
                raise CommandError(f'--item-for log id must be an integer, got "{log_id}"')
        return overrides

    def _select_logs(self, options):
        if options["log_ids"]:
            logs = Logs.objects.filter(pk__in=options["log_ids"])
            missing = set(options["log_ids"]) - set(logs.values_list("pk", flat=True))
            if missing:
                raise CommandError(f"No Logs row for id(s): {sorted(missing)}")
            return logs

        logs = Logs.objects.filter(log_project_name__iexact=options["source_project"])
        if options["task_contains"]:
            logs = logs.filter(log_tasks__icontains=options["task_contains"])
        if options["user"]:
            logs = logs.filter(user__username__iexact=options["user"])
        return logs

    # ------------------------------------------------------------------- main

    def handle(self, *args, **options):
        if options["inspect"]:
            self._inspect(options["project"])
            return

        project = self._resolve_project(options["project"])
        contract = self._resolve_contract(project, options["contract"])
        section = self._resolve_section(contract, options["section"])
        default_item = self._resolve_item(section, options["item"])

        overrides = self._parse_item_overrides(options["item_for"])
        override_items = {
            log_id: self._resolve_item(section, name) for log_id, name in overrides.items()
        }

        logs = self._select_logs(options).select_related(
            "user", "log_contract", "log_section", "log_Item"
        ).order_by("log_timestamps", "pk")

        count = logs.count()
        if not count:
            self.stdout.write(self.style.WARNING("No logs matched the selection — nothing to do."))
            return

        unknown = set(override_items) - set(logs.values_list("pk", flat=True))
        if unknown:
            raise CommandError(
                f"--item-for references log id(s) not in the selection: {sorted(unknown)}"
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Destination: {project.project_name} / {contract.contract_name} / "
                f"{section.section_name} / {default_item.Item_name}"
            )
        )
        self.stdout.write(f"{count} log(s) selected:\n")

        total_hours = 0.0
        for log in logs:
            target_item = override_items.get(log.pk, default_item)
            marker = "  *" if log.pk in override_items else "   "
            total_hours += float(log.log_time or 0)
            self.stdout.write(
                f"{marker} id={log.pk:<6} {log.log_timestamps:<20} {float(log.log_time or 0):>5.1f}h  "
                f"{(log.user.username if log.user else '-'):<6} "
                f"{log.log_project_name} / {log.log_contract.contract_name} / "
                f"{log.log_section.section_name} / {log.log_Item.Item_name}"
                f"  ->  {project.project_name} / {contract.contract_name} / "
                f"{section.section_name} / {target_item.Item_name}"
            )
            if len(log.log_tasks or "") > 0:
                self.stdout.write(f"        task: {log.log_tasks}")

        self.stdout.write(f"\nTotal: {count} log(s), {total_hours:.1f} h")

        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING("\nDRY RUN — nothing written. Re-run with --apply to commit.")
            )
            return

        with transaction.atomic():
            updated = 0
            for log in logs:
                log.log_project_name = project.project_name
                log.log_contract = contract
                log.log_section = section
                log.log_Item = override_items.get(log.pk, default_item)
                log.save(
                    update_fields=[
                        "log_project_name",
                        "log_contract",
                        "log_section",
                        "log_Item",
                    ]
                )
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"\nUpdated {updated} log(s)."))
