# Generated by Django 2.2.2 on 2019-07-16 20:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_cart', '0014_auto_20190716_2021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='inventory',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shopping_cart.Inventory'),
        ),
    ]