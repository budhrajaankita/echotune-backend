# Generated by Django 5.0.3 on 2024-03-19 19:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('echoapp', '0003_source_rename_id_guestprofile_session_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='guestprofile',
            old_name='interests',
            new_name='topics',
        ),
    ]