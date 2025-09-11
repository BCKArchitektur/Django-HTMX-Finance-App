
from django.db import migrations

def backfill_ar_numbers(apps, schema_editor):
    Invoice = apps.get_model('tracker', 'Invoice')
    from django.db import transaction

    with transaction.atomic():
        contract_ids = (Invoice.objects
                        .filter(invoice_type='AR')
                        .values_list('contract_id', flat=True)
                        .distinct())

        for cid in contract_ids:
            ar_qs = (Invoice.objects
                     .filter(invoice_type='AR', contract_id=cid)
                     .order_by('created_at', 'id'))
            n = 0
            to_update = []
            for inv in ar_qs:
                n += 1
                if inv.current_ar_number != n:
                    inv.current_ar_number = n
                    to_update.append(inv)
            if to_update:
                Invoice.objects.bulk_update(to_update, ['current_ar_number'])

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0063_invoice_current_ar_number'),
    ]

    operations = [
        migrations.RunPython(backfill_ar_numbers, migrations.RunPython.noop),
    ]
