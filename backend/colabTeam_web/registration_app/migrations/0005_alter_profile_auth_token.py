# Generated by Django 4.2.7 on 2023-11-17 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registration_app", "0004_alter_profile_profilepic"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="auth_token",
            field=models.CharField(
                default="5351efeb-e62d-44cc-8180-9617c842b540", max_length=100
            ),
        ),
    ]