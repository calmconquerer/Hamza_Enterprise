# Generated by Django 2.2 on 2019-07-10 05:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20190622_0805'),
        ('transaction', '0009_saledetail_hs_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saledetail',
            name='item_code',
        ),
        migrations.RemoveField(
            model_name='saledetail',
            name='item_description',
        ),
        migrations.RemoveField(
            model_name='saledetail',
            name='item_name',
        ),
        migrations.RemoveField(
            model_name='saledetail',
            name='unit',
        ),
        migrations.AddField(
            model_name='saledetail',
            name='item_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.Add_products'),
        ),
    ]
