# Generated by Django 2.2 on 2019-07-07 19:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0002_auto_20190625_0959'),
        ('customer', '0006_auto_20190707_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotationheadercustomer',
            name='company_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='supplier.Company_info'),
        ),
    ]
