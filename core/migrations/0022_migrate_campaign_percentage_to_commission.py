# Generated manually: copy percentage to commission_value

from django.db import migrations


def migrate_percentage_to_commission(apps, schema_editor):
    Campaign = apps.get_model('core', 'Campaign')
    for campaign in Campaign.objects.all():
        if campaign.percentage is not None:
            campaign.commission_type = 'percentage'
            campaign.commission_value = campaign.percentage
            campaign.save(update_fields=['commission_type', 'commission_value'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_add_campaign_commission_type_value'),
    ]

    operations = [
        migrations.RunPython(migrate_percentage_to_commission, noop),
    ]
