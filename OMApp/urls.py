from django.urls import path
from OMApp import views

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    #url(r'^api/orders$', views.order_list),
    #url(r'^api/orderDetails/(?P<pk>[0-9]+)$',),
    #url(r'^api/inventory$',views.inventory_list),
    #url(r'^api/orderDetails/(?P<pk>[0-9]+)/Status$',)
    #url(r'^api/Delivered$',views.)
    path('orders/<order_id>' , views.order , name='order'),
]
