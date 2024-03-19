# Generated by Django 5.0.3 on 2024-03-19 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('echoapp', '0002_guestprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RenameField(
            model_name='guestprofile',
            old_name='id',
            new_name='session_id',
        ),
        migrations.RemoveField(
            model_name='guestprofile',
            name='created',
        ),
        migrations.RemoveField(
            model_name='guestprofile',
            name='topics',
        ),
        migrations.AddField(
            model_name='guestprofile',
            name='interests',
            field=models.ManyToManyField(related_name='guest_profiles', to='echoapp.topic'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='topics',
            field=models.ManyToManyField(related_name='user_profiles', to='echoapp.topic'),
        ),
        migrations.AddField(
            model_name='guestprofile',
            name='sources',
            field=models.ManyToManyField(related_name='guest_profiles', to='echoapp.source'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='sources',
            field=models.ManyToManyField(related_name='user_profiles', to='echoapp.source'),
        ),
    ]
