# Generated by Django 2.2.2 on 2019-07-16 18:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_cart', '0006_auto_20190716_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='inventory',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='shopping_cart.Inventory'),
        ),
    ]
