# Generated by Django 2.2.2 on 2019-07-11 03:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_cart', '0002_auto_20190711_0307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='owner',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.Profile'),
        ),
    ]