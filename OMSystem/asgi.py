"""
ASGI config for OMSystem project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from django.core.asgi import get_asgi_application
from OMApp.consumers import OrderProgress

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OMSystem.settings')

application = get_asgi_application()

ws_pattern= [
    path('ws/orders/<order_id>', OrderProgress.as_asgi()),
]

application= ProtocolTypeRouter(
    {
        'websocket':AuthMiddlewareStack(URLRouter(ws_pattern))
    }
)