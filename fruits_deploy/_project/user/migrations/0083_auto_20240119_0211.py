# Generated by Django 3.2.23 on 2024-01-19 00:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0082_auto_20240119_0113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='date',
            field=models.DateField(default=datetime.date(2024, 1, 19)),
        ),
        migrations.AlterField(
            model_name='sale',
            name='date',
            field=models.DateField(default=datetime.date(2024, 1, 19)),
        ),
        migrations.AlterField(
            model_name='seller',
            name='date',
            field=models.DateField(default=datetime.date(2024, 1, 19)),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='date',
            field=models.DateField(default=datetime.date(2024, 1, 19)),
        ),
    ]
