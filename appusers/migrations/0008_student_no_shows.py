# Generated by Django 4.2 on 2023-04-24 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appusers', '0007_availability_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='no_shows',
            field=models.IntegerField(default=0, max_length=1),
        ),
    ]
