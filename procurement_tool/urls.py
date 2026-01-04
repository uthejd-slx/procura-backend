"""
URL configuration for procurement_tool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/", include("accounts.urls")),
    path("api/", include("profiles.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("boms.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("purchase_orders.urls")),
    path("api/", include("attachments.urls")),
    path("api/", include("searches.urls")),
    path("api/", include("assets.urls")),
    path("api/", include("transfers.urls")),
    path("api/", include("bills.urls")),
    path("api/", include("feedback.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
