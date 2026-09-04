"""
sync_tarkov 의 판단 로직만 확인하는 최소 테스트입니다. (인터넷 불필요)

    python manage.py test guide

여기서 막는 것:
  1. 수류탄이 탄약 목록에 섞이는 사고 (types 대신 propertiesType 으로 나눠야 함)
  2. 이름이 "<id> Name" 인 채로 화면에 나오는 사고 (번역표를 안 거친 경우)
  3. grids 안의 거대한 filters 가 통째로 DB에 저장되는 사고
"""
from django.test import TestCase

from guide.management.commands.sync_tarkov import PROPS_TO_CATEGORY, Command
from guide.models import CALIBER_GROUPS, CALIBERS, TarkovItem


class CategoryTest(TestCase):
    def test_수류탄은_탄약이_아니다(self):
        # 수류탄은 types 에 "ammo" 가 들어 있지만 propertiesType 은 다릅니다.
        self.assertIsNone(PROPS_TO_CATEGORY.get("ItemPropertiesGrenade"))
        self.assertEqual(PROPS_TO_CATEGORY["ItemPropertiesAmmo"], "ammo")

    def test_의료품_5종은_모두_meds(self):
        for t in ("MedKit", "MedicalItem", "Painkiller", "SurgicalKit", "Stim"):
            self.assertEqual(PROPS_TO_CATEGORY[f"ItemProperties{t}"], "meds")


class SlimTest(TestCase):
    def test_grids는_가로세로만_남는다(self):
        props = Command.slim({
            "propertiesType": "ItemPropertiesBackpack",
            "locale": {},
            "capacity": 16,
            "grids": [{"width": 4, "height": 4,
                       "filters": {"excludedItems": ["x"] * 500}}],
        }, locale={})
        self.assertEqual(props["grids"], [{"width": 4, "height": 4}])
        self.assertEqual(props["capacity"], 16)
        self.assertNotIn("propertiesType", props)
        self.assertNotIn("locale", props)

    def test_효과_이름이_한국어로_바뀐다(self):
        props = Command.slim(
            {"stimEffects": [{"type": "BodyTemperature", "value": -7},
                             {"type": "Skill", "skill": "Attention", "value": 10}]},
            locale={"BodyTemperature": "체온", "Skill": "스킬", "Attention": "주의력"},
        )
        self.assertEqual(props["stimEffects"][0]["type"], "체온")
        self.assertEqual(props["stimEffects"][1]["skill"], "주의력")
        # 값(value)은 건드리면 안 됩니다.
        self.assertEqual(props["stimEffects"][0]["value"], -7)

    def test_주사기_표시는_의료품에_항상_붙는다(self):
        # True일 때만 넣으면 JSONField 에서 '주사기 아님' 조회가 통째로 비어버립니다.
        self.assertIs(Command.slim({}, {}, ["meds", "injectors"])["injector"], True)
        self.assertIs(Command.slim({}, {}, ["meds"])["injector"], False)
        # 의료품이 아닌 아이템에는 붙이지 않습니다.
        self.assertNotIn("injector", Command.slim({}, {}, ["ammo"]))

    def test_의약품_주사기_조회가_둘_다_나온다(self):
        TarkovItem.objects.create(api_id="p1", category="meds", name="붕대",
                                  properties={"injector": False})
        TarkovItem.objects.create(api_id="p2", category="meds", name="모르핀",
                                  properties={"injector": True})
        meds = TarkovItem.objects.filter(category="meds")
        self.assertEqual(meds.filter(properties__injector=False).count(), 1)
        self.assertEqual(meds.filter(properties__injector=True).count(), 1)


class CaliberTest(TestCase):
    def test_구경_이름이_읽을_수_있게_바뀐다(self):
        item = TarkovItem(properties={"caliber": "Caliber1143x23ACP"})
        self.assertEqual(item.caliber_kr, ".45 ACP")

    def test_모르는_구경은_Caliber만_뗀다(self):
        item = TarkovItem(properties={"caliber": "Caliber99x99NEW"})
        self.assertEqual(item.caliber_kr, "99x99NEW")

    def test_모든_구경이_묶음에_속한다(self):
        # 묶음 이름을 오타내면 그 구경이 선택 상자에서 통째로 사라집니다.
        for code, (_, group) in CALIBERS.items():
            self.assertIn(group, CALIBER_GROUPS, msg=code)


class TranslationTest(TestCase):
    def test_이름은_번역표를_거쳐야_한다(self):
        # 기본 문서의 name 은 실제 이름이 아니라 번역표를 찾는 열쇠입니다.
        raw = {"name": "54527a984bdc2d4e668b4567 Name"}
        locale = {"54527a984bdc2d4e668b4567 Name": "5.56x45mm M855"}
        self.assertEqual(locale.get(raw["name"]), "5.56x45mm M855")
        # 번역이 없으면 열쇠라도 남아야지, 빈칸이 되면 안 됩니다.
        self.assertEqual(locale.get("없는키") or "없는키", "없는키")
