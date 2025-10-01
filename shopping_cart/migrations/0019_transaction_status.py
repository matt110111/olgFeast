# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_cart', '0018_rename_invetory_item_inventory_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('preparing', 'Preparing'), ('ready', 'Ready'), ('complete', 'Complete')], default='pending', max_length=20),
        ),
    ]
