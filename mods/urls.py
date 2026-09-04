from django.urls import path

from . import views

app_name = "mods"

urlpatterns = [
    path("", views.index, name="index"),
    path("presets/", views.presets, name="presets"),
    path("weapons/", views.weapons, name="weapons"),
    path("weapons/<str:api_id>/", views.weapon_detail, name="weapon_detail"),
    path("parts/", views.parts, name="parts"),
]
