# Generated by Django 4.1.4 on 2023-08-27 09:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stock", "0003_remove_stock_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="stock",
            name="type",
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]
