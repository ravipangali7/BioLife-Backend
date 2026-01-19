# Generated manually for adding order field to Category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_category_is_featured'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.IntegerField(blank=True, help_text='Display order (auto-incremented if empty or duplicate)', null=True, unique=True),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['order', 'name'], 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
    ]
