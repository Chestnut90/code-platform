# Generated by Django 4.1.7 on 2023-03-14 08:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("problems", "0005_alter_problem_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="category",
            old_name="category",
            new_name="name",
        ),
    ]