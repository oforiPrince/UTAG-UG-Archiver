# Generated by Django 4.2.6 on 2024-05-04 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_alter_announcement_target_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='announcement',
            name='is_published',
        ),
        migrations.AddField(
            model_name='announcement',
            name='status',
            field=models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('ARCHIVED', 'Archived')], default='DRAFT', max_length=20),
        ),
    ]