# Generated by Django 2.2.8 on 2020-01-02 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deeds', '0003_alter_field_data_on_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='unknown',
            field=models.BooleanField(default=False),
        ),
    ]