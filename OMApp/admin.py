from django.contrib import admin
from OMApp.models import Inventory, OrderDetails, OrderItems, DeliveryTeam

# Register your models here.
admin.site.register(Inventory)
admin.site.register(OrderDetails)
admin.site.register(OrderItems)
admin.site.register(DeliveryTeam)