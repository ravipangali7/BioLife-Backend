# Generated manually to remove commission and task systems

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_setting_user_refer_amount'),
    ]

    operations = [
        # Remove sale_commision field from Setting
        migrations.RemoveField(
            model_name='setting',
            name='sale_commision',
        ),
        # Delete Task-related models
        migrations.DeleteModel(
            name='UserTaskLink',
        ),
        migrations.DeleteModel(
            name='UserTaskImage',
        ),
        migrations.DeleteModel(
            name='UserTask',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
    ]
