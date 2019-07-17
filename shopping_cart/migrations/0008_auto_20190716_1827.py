# Generated by Django 2.2.2 on 2019-07-16 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_cart', '0007_auto_20190716_1816'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='inventory',
        ),
        migrations.AddField(
            model_name='transaction',
            name='inventory',
            field=models.ManyToManyField(to='shopping_cart.Inventory'),
        ),
    ]
