# Generated by Django 5.2 on 2025-04-03 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statements', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='statement',
            constraint=models.UniqueConstraint(fields=('account', 'date'), name='unique_account_date_pair'),
        ),
    ]
