import json
import datetime
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from rest_framework import status

from OMApp.models import Inventory, OrderDetails, DeliveryTeam
from OMApp.Serializers.InventorySerializer import InventorySerializer
from OMApp.Serializers.OrderDetailsSerializer import OrderDetailsSerializer
from OMApp.Serializers.OrderItemsSerializer import OrderItemsSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response


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

            estimateDeliveryTime, deliveryTeam, deliveryStatus = process_order(orderDetailsSerializer.validated_data)

            order1 = orderDetailsSerializer.save()
            print("Ordered Saved")
            amount = SaveOrderItem(orders_data, order1)

            #push order to the queue
            if(deliveryTeam == None and deliveryStatus == None):
                OrderDetails.order_queue.append(order1.pk)
                print("order queue")
                print(OrderDetails.order_queue)
            
            #Incase order item contains any item count which is not present in inventory
            if(amount == -1):
                OrderDetails.objects.filter(Order_Number=order1.pk).delete()
                return Response(data="Order Not added because not suffcient item present in Inventory or Order Item format wrong", status=status.HTTP_400_BAD_REQUEST)

            if(deliveryTeam == None):
                OrderDetails.objects.filter(
                    Order_Number=order1.pk).update(Total_Amount=amount, Estimated_Delivery_Time=estimateDeliveryTime)
            else:
                OrderDetails.objects.filter(
                    Order_Number=order1.pk).update(Total_Amount=amount, Estimated_Delivery_Time=estimateDeliveryTime, DeliveryTeam=deliveryTeam, Status=deliveryStatus)

            return Response(data="Order Added", status=status.HTTP_201_CREATED)
        return Response(data="Order Format wrong", status=status.HTTP_400_BAD_REQUEST)


def SaveOrderItem(orders_data, order1):

    for order in orders_data['OrderItems']:
        inventoryForOrder = Inventory.objects.filter(Model_Number=order['Model_Number'])
        if inventoryForOrder[0].Units_Availabe < order['Count']:
            return -1

    amount = 0
    for order in orders_data['OrderItems']:
        inventoryForOrder = Inventory.objects.filter(
            Model_Number=order['Model_Number'])

        remainingQuantity = inventoryForOrder[0].Units_Availabe - order['Count']
        Inventory.objects.filter(Model_Number=order['Model_Number']).update(Units_Availabe=remainingQuantity)

        amount += (inventoryForOrder[0].Price * order['Count'])

        order['Model_Number'] = inventoryForOrder[0].pk
        order['Order_Number'] = order1.pk
        orderItemsSerializer = OrderItemsSerializer(data=order)
        if orderItemsSerializer.is_valid():
            orderItemsSerializer.save()
        else:
            return -1
    return amount


def process_order(order):
    delivery_agent = DeliveryTeam.objects.filter(
        Status=DeliveryTeam.DeliveryTeamStatus.FREE)

    additionalTimeInMinForDelivery = 40 if order['Delivery_Distance'] <= 5 else 60
    additionalTimeToReturn = 20 if order['Delivery_Distance'] <= 5 else 40

    if delivery_agent is None or delivery_agent.count() == 0:
        placed_orders = OrderDetails.objects.filter(
            Status=OrderDetails.DeliveryStatusEnum.PLACED).order_by('-Estimated_Delivery_Time')
        
        if placed_orders is None or placed_orders.count() == 0:
            agent = DeliveryTeam.objects.order_by('Next_Activate_Time')
            agent_ActivationTime = agent[0].Next_Activate_Time
            estimated_delivey_time = agent_ActivationTime + \
                datetime.timedelta(minutes=additionalTimeInMinForDelivery)

        else:
            last_ordered_estimate_time = placed_orders[0].Estimated_Delivery_Time
            last_ordered_distance = placed_orders[0].Delivery_Distance
            additionalTimeToReturnForLastOrder = 20 if last_ordered_distance <= 5 else 40
            estimated_delivey_time = last_ordered_estimate_time + datetime.timedelta(
                minutes=(additionalTimeInMinForDelivery+additionalTimeToReturnForLastOrder))

        return estimated_delivey_time, None, None

    elif delivery_agent.count() == 1:
        estimated_delivey_time = get_estimated_delivery_time(
            additionalTimeInMinForDelivery)

        estimated_next_free_time = get_estimated_next_free_time(
            estimated_delivey_time, additionalTimeToReturn)

        delivery_agent_pk = delivery_agent[0].pk

        DeliveryTeam.objects.filter(pk=delivery_agent[0].pk).update(
            Status=DeliveryTeam.DeliveryTeamStatus.DELIVERING, Next_Activate_Time=estimated_next_free_time)

        return estimated_delivey_time, delivery_agent_pk, OrderDetails.DeliveryStatusEnum.INTRANSIT

    else:
        agent = DeliveryTeam.objects.order_by('Next_Activate_Time')
        delivery_team_id = agent[0].pk

        estimated_delivey_time = get_estimated_delivery_time(
            additionalTimeInMinForDelivery)

        estimated_next_free_time = get_estimated_next_free_time(
            estimated_delivey_time, additionalTimeToReturn)

        DeliveryTeam.objects.filter(pk=delivery_team_id).update(
            Status=DeliveryTeam.DeliveryTeamStatus.DELIVERING, Next_Activate_Time=estimated_next_free_time)

        return estimated_delivey_time, delivery_team_id, OrderDetails.DeliveryStatusEnum.INTRANSIT


def get_estimated_delivery_time(additionalTimeInMinForDelivery):
    return datetime.datetime.now() + datetime.timedelta(minutes=additionalTimeInMinForDelivery)


def get_estimated_next_free_time(estimated_delivey_time, additionalTimeToReturn):
    return estimated_delivey_time + datetime.timedelta(minutes=additionalTimeToReturn)


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

def order(request , order_id):
    order = OrderDetails.objects.filter(Order_Number=order_id).first()
    if order is None:
        return redirect('/')
    
    context = {'order' : order}
    return render(request , 'order.html', context)

@api_view(['PATCH'])
def order_delivered(request, delivery_team_id):
    delivery_team = DeliveryTeam.objects.get(pk=delivery_team_id)
    delivery_order = delivery_team.orderdetails_set.first()
    print(delivery_order)
    if delivery_order == None:
        return Response(data= "No Orders",status=status.HTTP_200_OK)

    #update the previous order
    OrderDetails.objects.filter(Order_Number=delivery_order.pk).update(Status=OrderDetails.DeliveryStatusEnum.COMPLETED)
    previous_order = OrderDetails.objects.get(pk=delivery_order.pk)
    previous_order.save() 
    delivery_team.orderdetails_set.clear()

    #get the next from queue
    order_queue = OrderDetails.order_queue

    if len(order_queue) == 0:
        DeliveryTeam.objects.filter(pk=delivery_team.pk).update(Status=DeliveryTeam.DeliveryTeamStatus.FREE)
        return Response(data= "Order Delivered, Nothing to Deliver",status=status.HTTP_200_OK)
    else:
        next_order_pk = OrderDetails.order_queue[0]
        print(next_order_pk)
        OrderDetails.order_queue.pop(0)

        print("current order queue status")
        print(OrderDetails.order_queue)

        #update the next order
        OrderDetails.objects.filter(Order_Number=next_order_pk).update(DeliveryTeam=delivery_team.pk, Status=OrderDetails.DeliveryStatusEnum.INTRANSIT)
        next_order = OrderDetails.objects.get(pk=next_order_pk)
        next_order.save()      
        return Response(data= "Order Delivered, New Order in Delivery",status=status.HTTP_200_OK)