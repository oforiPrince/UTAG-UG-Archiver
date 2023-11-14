# Generated by Django 4.2.6 on 2023-10-21 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_executive_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executiveposition',
            name='name',
            field=models.CharField(choices=[('President', 'President'), ('Vice President', 'Vice President'), ('Secretary', 'Secretary'), ('Treasurer', 'Treasurer'), ('Committee Member', 'Committee Member')], max_length=30, unique=True),
        ),
    ]
