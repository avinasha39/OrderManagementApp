from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
import datetime
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
import json


def increment_order_id():
    todayDate = datetime.datetime.now().date()
    today_order_list = OrderDetails.objects.filter( Placed_Time__year=todayDate.year,
                                                    Placed_Time__month=todayDate.month,
                                                    Placed_Time__day=todayDate.day)
    #print(today_order_list)
    if today_order_list == None or today_order_list.count() == 0:
        return datetime.datetime.now().strftime("%Y-%m-%d")+'_'+'1'

    return datetime.datetime.now().strftime("%Y-%m-%d")+'_'+ str(today_order_list.count() +1)


class Inventory(models.Model):
    Category = models.CharField(max_length=20, null=False)
    Model_Number = models.CharField(max_length=15, unique=True)
    Units_Availabe = models.IntegerField(
        validators=[MinValueValidator(0)], default=0)
    Price = models.DecimalField(max_digits=100, decimal_places=2)


class DeliveryTeam(models.Model):

    class DeliveryTeamStatus(models.TextChoices):
        FREE = 'FR', _('FREE')
        DELIVERING = 'DL', _('DELIVERING')

    Status = models.CharField(
        max_length=2,  choices=DeliveryTeamStatus.choices, default=DeliveryTeamStatus.FREE)
    Next_Activate_Time = models.DateTimeField (default= datetime.datetime.now())


class OrderDetails(models.Model):

    order_queue = []

    class DeliveryStatusEnum(models.TextChoices):
        PLACED = 'PL', _('PLACED')
        INTRANSIT = 'IN', _('INTRANSIT')
        COMPLETED = 'CO', _('COMPLETED')
        FAILED = 'FL', _('FAILED')

    Order_Number = models.CharField(primary_key=True, 
                                    max_length=20, default=increment_order_id, editable=False)                                
    Placed_Time = models.DateTimeField(default= datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    Customer_name = models.CharField(max_length=20)
    Customer_add = models.TextField()
    Delivery_Distance = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(10)])
    Estimated_Delivery_Time = models.DateTimeField(default= datetime.datetime.now())
    Total_Amount = models.DecimalField(
        max_digits=100, decimal_places=2, default=0)
    DeliveryTeam = models.ForeignKey(DeliveryTeam, on_delete=models.DO_NOTHING, null=True)
    Status = models.CharField(
        max_length=20,  choices=DeliveryStatusEnum.choices, default=DeliveryStatusEnum.PLACED)
    
    @staticmethod
    def give_order_details(order_id):
        instance = OrderDetails.objects.filter(Order_Number=order_id).first()
        status = instance.get_Status_display()
        data  = {}
        data['order_id'] = instance.Order_Number
        data['amount'] = str(instance.Total_Amount)
        data['status'] = status
        data['date'] = str(instance.Placed_Time)
        progress_percentage = 20
        if status == 'PLACED':
            progress_percentage = 20
        elif status == 'INTRANSIT':
            progress_percentage = 60
        elif status == 'COMPLETED':
            progress_percentage = 100
            
        data['progress'] = progress_percentage
        return data

@receiver(post_save, sender=OrderDetails)
def order_status_handler(sender, instance,created , **kwargs):
    
    if not created:
        print("######## Receiver ###########")
        channel_layer = get_channel_layer()
        data  = {}
        status = instance.get_Status_display()
        data['order_id'] = instance.Order_Number
        data['amount'] = str(instance.Total_Amount)
        data['status'] = status
        data['date'] = str(instance.Placed_Time)
        progress_percentage = 20
        if status == 'PLACED':
            progress_percentage = 20
        elif status == 'INTRANSIT':
            progress_percentage = 60
        elif status == 'COMPLETED':
            progress_percentage = 100
    
        data['progress'] = progress_percentage
        print(data)
        async_to_sync(channel_layer.group_send)(
            'order_%s' % instance.Order_Number,{
                'type': 'order_status',
                'value': json.dumps(data)
            }
        )


class OrderItems(models.Model):
    Model_Number = models.ForeignKey(
        Inventory, on_delete=models.DO_NOTHING)
    Count = models.IntegerField(validators=[MinValueValidator(1)])
    Order_Number = models.ForeignKey(
        OrderDetails, on_delete=models.CASCADE)
