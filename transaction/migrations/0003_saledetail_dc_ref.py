# Generated by Django 2.2 on 2019-06-25 05:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0002_auto_20190624_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='saledetail',
            name='dc_ref',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
