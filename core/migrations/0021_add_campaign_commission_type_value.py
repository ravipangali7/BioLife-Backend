# Generated manually for commission_type and commission_value

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_add_campaign_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='commission_type',
            field=models.CharField(
                choices=[('flat', 'Flat'), ('percentage', 'Percentage')],
                default='percentage',
                help_text='Reward type: flat amount or percentage of sale',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='campaign',
            name='commission_value',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Flat: amount in Rs per unit. Percentage: 0-100.',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Deprecated: use commission_type/commission_value',
                max_digits=5,
                null=True,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
            ),
        ),
    ]
