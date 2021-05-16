import json
import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from rest_framework import status

from OMApp.models import Inventory, OrderDetails, OrderItems, DeliveryTeam
from OMApp.Serializers.DeliveryTeamSerializer import DeliveryTeamSerializer
from OMApp.Serializers.InventorySerializer import InventorySerializer
from OMApp.Serializers.OrderDetailsSerializer import OrderDetailsSerializer
from OMApp.Serializers.OrderItemsSerializer import OrderItemsSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response


# return response (date = message+data, status = status.HTTP200)
# Create your views here.
@api_view(['GET', 'POST'])
def order_list(request):
    if request.method == 'GET':
        orders = OrderDetails.objects.all()
        order_list = []
        for order in orders:
            tempdict = {"Order_Number": order.pk,
                        "Placed_Time": order.Placed_Time}
            order_list.append(tempdict)

        orderDict = {"orders": order_list}
        return Response(data=orderDict, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        orders_data = json.loads(request.body)
        orderDetailsSerializer = OrderDetailsSerializer(
            data=orders_data['OrderDetails'])

        if orderDetailsSerializer.is_valid():
            order1 = orderDetailsSerializer.save()
            amount = SaveOrderItem(orders_data, order1)
            OrderDetails.objects.filter(
                Order_Number=order1.pk).update(Total_Amount=amount)

            process_order(order1)

            return Response(data="Order Added", status=status.HTTP_201_CREATED)
        return Response(data="Order Format wrong", status=status.HTTP_400_BAD_REQUEST)


def SaveOrderItem(orders_data, order1):
    amount = 0
    for order in orders_data['OrderItems']:
        print(order)
        inventory1 = Inventory.objects.filter(
            Model_Number=order['Model_Number'])
        amount += (inventory1[0].Price * order['Count'])
        order['Model_Number'] = inventory1[0].pk
        order['Order_Number'] = order1.pk
        orderItemsSerializer = OrderItemsSerializer(data=order)
        print(order)
        if orderItemsSerializer.is_valid():
            orderItemsSerializer.save()
        else:
            print("wrong format")
    return amount


def process_order(order):
    delivery_agent = DeliveryTeam.objects.filter(
        Status=DeliveryTeam.DeliveryTeamStatus.FREE)

    additionalTimeInMinForDelivery = 40 if order.Delivery_Distance <= 5 else 60
    additionalTimeToReturn = 20 if order.Delivery_Distance <= 5 else 40
    print("additionalTimeInMinForDelivery" + str(additionalTimeInMinForDelivery))

    if delivery_agent is None or delivery_agent.count() == 0:
        placed_orders = OrderDetails.objects.filter(Status = OrderDetails.DeliveryStatusEnum.PLACED).order_by('-Placed_Time')
        print(placed_orders)
        if placed_orders is None or placed_orders.count() == 0:
            agent = DeliveryTeam.objects.order_by('Next_Activate_Time')
            agent_ActivationTime = agent[0].Next_Activate_Time
            print("agent_ActivationTime" )
            print( agent_ActivationTime)
            estimated_delivey_time = agent_ActivationTime + datetime.timedelta(minutes=additionalTimeInMinForDelivery)

        else:
            print("in else")
            last_ordered_estimate_time = placed_orders[0].Estimated_Delivery_Time
            last_ordered_distance = placed_orders[0].Delivery_Distance
            additionalTimeToReturnForLastOrder = 20 if last_ordered_distance <= 5 else 40
            estimated_delivey_time = last_ordered_estimate_time + datetime.timedelta(minutes=(additionalTimeInMinForDelivery+additionalTimeToReturnForLastOrder))

        print("estimated_delivey_time" )
        print(estimated_delivey_time)
        OrderDetails.objects.filter(Order_Number=order.pk).update(Estimated_Delivery_Time=estimated_delivey_time)

    elif delivery_agent.count() == 1:
        estimated_delivey_time = get_estimated_delivery_time(
            additionalTimeInMinForDelivery)

        estimated_next_free_time = get_estimated_next_free_time(
            estimated_delivey_time, additionalTimeToReturn)

        OrderDetails.objects.filter(
            Order_Number=order.pk).update(Estimated_Delivery_Time=estimated_delivey_time, DeliveryTeam=delivery_agent[0].pk, Status=OrderDetails.DeliveryStatusEnum.INTRANSIT)

        DeliveryTeam.objects.filter(pk=delivery_agent[0].pk).update(
            Status=DeliveryTeam.DeliveryTeamStatus.DELIVERING, Next_Activate_Time=estimated_next_free_time)
    else:
        agent = DeliveryTeam.objects.order_by('Next_Activate_Time')

        estimated_delivey_time = get_estimated_delivery_time(
            additionalTimeInMinForDelivery)

        estimated_next_free_time = get_estimated_next_free_time(
            estimated_delivey_time, additionalTimeToReturn)

        OrderDetails.objects.filter(
            Order_Number=order.pk).update(Estimated_Delivery_Time=estimated_delivey_time, DeliveryTeam=agent[0].pk, Status=OrderDetails.DeliveryStatusEnum.INTRANSIT)

        DeliveryTeam.objects.filter(pk=agent[0].pk).update(
            Status=DeliveryTeam.DeliveryTeamStatus.DELIVERING, Next_Activate_Time=estimated_next_free_time)


def get_estimated_delivery_time(additionalTimeInMinForDelivery):
    return datetime.datetime.now() + datetime.timedelta(minutes=additionalTimeInMinForDelivery)


def get_estimated_next_free_time(estimated_delivey_time, additionalTimeToReturn):
    return  estimated_delivey_time + datetime.timedelta(minutes=additionalTimeToReturn)


@api_view(['GET', 'POST'])
def inventory_list(request):
    if request.method == 'GET':
        inventoryList = Inventory.objects.all()
        inventorySerializer = InventorySerializer(inventoryList, many=True)
        return Response(data=inventorySerializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        inventory_data = JSONParser.parse(request)
        inventorySerializer = InventorySerializer(data=inventory_data.data)
        if inventorySerializer.is_valid:
            inventorySerializer.save()
            return Response(data="Inventory updated", status=status.HTTP_201_CREATED)
        return Response(data="Inventory Format worng", status=status.HTTP_400_BAD_REQUEST)


# def deliveryAgent_list(request):
