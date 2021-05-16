# Generated by Django 3.2.1 on 2021-05-16 13:54

import OMApp.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Status', models.CharField(choices=[('FR', 'FREE'), ('DL', 'DELIVERING')], default='FR', max_length=2)),
                ('Next_Activate_Time', models.TimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Category', models.CharField(max_length=20)),
                ('Model_Number', models.CharField(max_length=15, unique=True)),
                ('Units_Availabe', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('Price', models.DecimalField(decimal_places=2, max_digits=100)),
            ],
        ),
        migrations.CreateModel(
            name='OrderDetails',
            fields=[
                ('Order_Number', models.CharField(default=OMApp.models.increment_order_id, editable=False, max_length=20, primary_key=True, serialize=False)),
                ('Placed_Time', models.DateField(auto_now_add=True)),
                ('Customer_name', models.CharField(max_length=20)),
                ('Customer_add', models.TextField()),
                ('Delivery_Distance', models.FloatField(validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(10)])),
                ('Estimated_Delivery_Time', models.TimeField(auto_now_add=True)),
                ('Total_Amount', models.DecimalField(decimal_places=2, default=0, max_digits=100)),
                ('Status', models.CharField(choices=[('PL', 'PLACED'), ('IN', 'INTRANSIT'), ('CO', 'COMPLETED'), ('FL', 'FAILED')], default='PL', max_length=20)),
                ('DeliveryTeam', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='OMApp.deliveryteam')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItems',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Count', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('Model_Number', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='OMApp.inventory')),
                ('Order_Number', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='OMApp.orderdetails')),
            ],
        ),
    ]
