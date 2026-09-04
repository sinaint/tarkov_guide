from django.contrib import admin

from .models import Mod, Preset, SlotOption, Weapon


@admin.register(Weapon)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ("name", "caliber", "ergonomics", "recoil_vertical", "price")
    search_fields = ("name", "caliber")


@admin.register(Preset)
class PresetAdmin(admin.ModelAdmin):
    list_display = ("name", "base_name", "ergonomics", "recoil_vertical", "price")
    search_fields = ("name", "base_name")


@admin.register(Mod)
class ModAdmin(admin.ModelAdmin):
    list_display = ("name", "mod_type", "ergonomics", "recoil_modifier", "price")
    list_filter = ("mod_type",)
    search_fields = ("name",)


@admin.register(SlotOption)
class SlotOptionAdmin(admin.ModelAdmin):
    list_display = ("weapon", "slot_name", "mod")
    search_fields = ("weapon__name", "slot_name", "mod__name")
