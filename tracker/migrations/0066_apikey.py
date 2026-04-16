from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0065_alter_client_city_alter_client_client_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Human-readable label for this key, e.g. 'HR App \u2013 Production'.", max_length=100)),
                ('key', models.CharField(db_index=True, editable=False, max_length=64, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
            },
        ),
    ]
