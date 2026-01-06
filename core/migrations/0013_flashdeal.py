# Generated manually for FlashDeal model

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_orderitem_stock_deducted'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlashDeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('discount_type', models.CharField(choices=[('flat', 'Flat'), ('percentage', 'Percentage')], max_length=20)),
                ('discount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='flash_deals/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('products', models.ManyToManyField(related_name='flash_deals', to='core.product')),
            ],
            options={
                'verbose_name': 'Flash Deal',
                'verbose_name_plural': 'Flash Deals',
                'ordering': ['-created_at'],
            },
        ),
    ]
