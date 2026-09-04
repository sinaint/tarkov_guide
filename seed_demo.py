"""API 연결 없이 화면이 잘 뜨는지 확인하기 위한 가짜 데이터"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from guide.models import TarkovItem

TarkovItem.objects.all().delete()

TarkovItem.objects.create(
    api_id="m1", category="meds", name="살레와 응급 처치 키트", short_name="살레와",
    width=1, height=1, base_price=15000, avg_24h_price=21000,
    properties={"hitpoints": 400, "useTime": 3, "maxHealPerUse": 85,
                "cures": ["HeavyBleeding"], "hpCostHeavyBleeding": 175},
)
TarkovItem.objects.create(
    api_id="m2", category="meds", name="프로펜탈", short_name="프로펜탈",
    width=1, height=1, base_price=9000, avg_24h_price=12000,
    properties={"useTime": 2, "cures": ["Pain", "Tremor"],
                "stimEffects": [{"type": "Pain", "value": 0, "duration": 200, "percent": False},
                                {"type": "Strength", "value": -3, "duration": 300, "percent": True}]},
)
TarkovItem.objects.create(
    api_id="b1", category="backpack", name="트라이 집 백팩", short_name="트라이집",
    width=4, height=5, base_price=60000, avg_24h_price=72000,
    properties={"capacity": 35, "speedPenalty": -0.05, "turnPenalty": -0.02,
                "grids": [{"width": 5, "height": 5}, {"width": 2, "height": 5}]},
)
TarkovItem.objects.create(
    api_id="r1", category="rig", name="6B5-15 방탄 리그", short_name="6B5",
    width=3, height=4, base_price=40000, avg_24h_price=None,
    properties={"capacity": 10, "class": 4, "ergoPenalty": -3,
                "grids": [{"width": 1, "height": 2}, {"width": 1, "height": 2},
                          {"width": 2, "height": 1}, {"width": 2, "height": 2}]},
)
TarkovItem.objects.create(
    api_id="a1", category="ammo", name="5.45x39mm BS", short_name="BS",
    width=1, height=1, base_price=800, avg_24h_price=1100,
    properties={"caliber": "Caliber545x39", "damage": 40, "penetrationPower": 51,
                "armorDamage": 60, "fragmentationChance": 0.05, "initialSpeed": 830,
                "tracer": False, "projectileCount": 1},
)
TarkovItem.objects.create(
    api_id="a2", category="ammo", name="12/70 버크샷", short_name="버크샷",
    width=1, height=1, base_price=200, avg_24h_price=350,
    properties={"caliber": "Caliber12g", "damage": 50, "penetrationPower": 3,
                "armorDamage": 12, "projectileCount": 8, "tracer": False},
)
print("seeded:", TarkovItem.objects.count())
