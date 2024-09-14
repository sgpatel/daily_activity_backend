# Generated by Django 5.1.1 on 2024-09-14 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('audio_path', models.CharField(blank=True, max_length=255)),
                ('transcript', models.TextField(blank=True)),
                ('summary', models.TextField(blank=True)),
                ('reminders', models.TextField(blank=True)),
                ('spending', models.FloatField(default=0)),
            ],
        ),
    ]
