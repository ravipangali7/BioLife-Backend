# Generated manually: remove deprecated percentage field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_migrate_campaign_percentage_to_commission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='percentage',
        ),
    ]
