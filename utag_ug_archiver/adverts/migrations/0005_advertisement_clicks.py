# Generated by Django 4.2.6 on 2024-05-04 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adverts', '0004_alter_advertisement_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='clicks',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
