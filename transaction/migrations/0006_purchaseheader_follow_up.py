# Generated by Django 2.2 on 2019-06-30 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0005_voucherheader_voucher_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseheader',
            name='follow_up',
            field=models.DateField(blank=True, default='2010-06-12'),
            preserve_default=False,
        ),
    ]
