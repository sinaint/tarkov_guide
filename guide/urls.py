from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("meds/", views.meds, name="meds"),
    path("storage/", views.storage, name="storage"),
    path("ammo/", views.ammo, name="ammo"),
]
