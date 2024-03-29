# Generated by Django 2.2.2 on 2019-07-11 01:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ref_code', models.CharField(max_length=40)),
                ('date_ordered', models.DateTimeField(auto_now_add=True)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_group', models.CharField(max_length=40)),
                ('name', models.CharField(max_length=40)),
                ('description', models.TextField(max_length=200, null=True)),
                ('value', models.FloatField(default=0.0)),
                ('ticket', models.IntegerField(default=1)),
                ('invetory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopping_cart.Inventory')),
            ],
        ),
    ]
