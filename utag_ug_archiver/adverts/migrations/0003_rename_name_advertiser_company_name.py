# Generated by Django 4.2.6 on 2024-05-04 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adverts', '0002_alter_advertisement_end_date_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='advertiser',
            old_name='name',
            new_name='company_name',
        ),
    ]
