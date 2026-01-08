# Generated manually for adding is_featured field to Category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_shippingcharge_order_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Show in header category bar'),
        ),
    ]
