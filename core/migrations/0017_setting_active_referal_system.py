# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_category_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='active_referal_system',
            field=models.BooleanField(default=False, help_text='Enable/disable referral and earn system'),
        ),
    ]
