"""
총기 모딩 데이터 모델

기존 guide 앱은 전혀 건드리지 않는 독립 앱입니다.

설계 요약:
  Weapon     — 총기 본체 (슬롯 목록을 JSON으로 보관)
  Preset     — 이미 조립이 끝난 완성품 (1단계)
  Mod        — 부품 하나 (3단계)
  SlotOption — "이 총의 이 슬롯에 이 부품이 들어간다" 연결 (2단계)

SlotOption 이 핵심입니다.
총기 × 슬롯 × 장착가능부품 조합이라 행 수가 수만 개가 될 수 있는데,
SQLite 는 이 정도는 가볍게 처리합니다. 대신 화면에서는 항상
상위 N개만 잘라서 보여줘야 합니다. (전부 뿌리면 브라우저가 멈춥니다)
"""
from django.db import models

# 구경 이름표는 guide 앱이 이미 갖고 있습니다. 같은 표를 두 벌 두면
# 패치 때 한쪽만 고치는 사고가 나므로 그대로 가져다 씁니다.
# (읽기만 하므로 guide 앱은 건드리지 않습니다)
from guide.models import CALIBERS


class Weapon(models.Model):
    """총기 본체"""

    api_id = models.CharField("API ID", max_length=64, primary_key=True)
    name = models.CharField("이름", max_length=255)
    short_name = models.CharField("축약명", max_length=100, blank=True)

    icon_link = models.URLField("아이콘", max_length=500, blank=True)
    wiki_link = models.URLField("위키", max_length=500, blank=True)

    caliber = models.CharField("구경", max_length=80, blank=True, db_index=True)

    # 맨몸 상태(부품 없음)의 기본 수치
    ergonomics = models.FloatField("조준편의", null=True, blank=True)
    recoil_vertical = models.IntegerField("세로 반동", null=True, blank=True)
    recoil_horizontal = models.IntegerField("가로 반동", null=True, blank=True)
    fire_rate = models.IntegerField("연사속도(RPM)", null=True, blank=True)

    price = models.IntegerField("가격", default=0)

    # 슬롯 목록 원본 (이름과 장착가능 개수 확인용)
    slots_raw = models.JSONField("슬롯 원본", default=list, blank=True)

    class Meta:
        verbose_name = "총기"
        verbose_name_plural = "총기"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def slot_count(self):
        return len(self.slots_raw or [])

    @property
    def caliber_kr(self):
        """Caliber127x55 → 12.7x55mm (탄약 페이지와 같은 이름표)"""
        if not self.caliber:
            return ""
        return CALIBERS.get(self.caliber, (self.caliber.removeprefix("Caliber"),))[0]


class Preset(models.Model):
    """공장 완성 프리셋 — 조립이 끝난 상태의 총"""

    api_id = models.CharField("API ID", max_length=64, primary_key=True)
    name = models.CharField("이름", max_length=255)

    # 어떤 총을 기반으로 한 프리셋인지
    base_weapon = models.ForeignKey(
        Weapon, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="presets", verbose_name="기반 총기",
    )
    base_name = models.CharField("기반 총기명", max_length=255, blank=True)

    icon_link = models.URLField("아이콘", max_length=500, blank=True)
    wiki_link = models.URLField("위키", max_length=500, blank=True)

    ergonomics = models.FloatField("조준편의", null=True, blank=True)
    recoil_vertical = models.IntegerField("세로 반동", null=True, blank=True)
    recoil_horizontal = models.IntegerField("가로 반동", null=True, blank=True)
    moa = models.FloatField("정확도(MOA)", null=True, blank=True)
    is_default = models.BooleanField("기본 프리셋", default=False)

    price = models.IntegerField("가격", default=0)

    class Meta:
        verbose_name = "프리셋"
        verbose_name_plural = "프리셋"
        ordering = ["base_name", "name"]

    def __str__(self):
        return self.name

    @property
    def score(self):
        """
        초보자용 종합 점수.
        조준편의는 높을수록, 반동은 낮을수록 좋으므로 부호를 뒤집어 더합니다.
        절대적 기준이 아니라 '같은 총 안에서 비교' 용도입니다.
        """
        ergo = self.ergonomics or 0
        rv = self.recoil_vertical or 0
        return round(ergo - rv * 0.5, 1)


class Mod(models.Model):
    """부품 하나"""

    api_id = models.CharField("API ID", max_length=64, primary_key=True)
    name = models.CharField("이름", max_length=255)
    short_name = models.CharField("축약명", max_length=100, blank=True)

    icon_link = models.URLField("아이콘", max_length=500, blank=True)
    wiki_link = models.URLField("위키", max_length=500, blank=True)

    # API 가 준 타입들 중 대표 1개 (suppressor, pistolGrip, mods 등)
    mod_type = models.CharField("부품 종류", max_length=40, blank=True, db_index=True)

    # ⚠️ 부호 주의!
    #   ergonomics       : 높을수록 좋음 (음수면 나빠짐)
    #   recoil_modifier  : 음수일수록 좋음 (-0.05 = 반동 5% 감소)
    ergonomics = models.FloatField("조준편의 변화", null=True, blank=True)
    recoil_modifier = models.FloatField("반동 변화율", null=True, blank=True)
    accuracy_modifier = models.FloatField("정확도 변화율", null=True, blank=True)

    price = models.IntegerField("가격", default=0)

    # 이 부품이 다시 갖는 하위 슬롯 (재귀 구조의 증거)
    slots_raw = models.JSONField("하위 슬롯", default=list, blank=True)

    class Meta:
        verbose_name = "부품"
        verbose_name_plural = "부품"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def recoil_percent(self):
        """반동 변화율을 사람이 읽는 % 로 변환. 음수 = 감소(좋음)"""
        if self.recoil_modifier is None:
            return None
        return round(self.recoil_modifier * 100, 1)

    @property
    def is_good_recoil(self):
        return self.recoil_modifier is not None and self.recoil_modifier < 0

    @property
    def is_good_ergo(self):
        return self.ergonomics is not None and self.ergonomics > 0

    @property
    def has_sub_slots(self):
        """하위 슬롯이 있으면 이 부품에 또 뭔가를 끼울 수 있다는 뜻"""
        return bool(self.slots_raw)

    @property
    def value_score(self):
        """
        가성비 점수 = (조준편의 상승 + 반동 감소량) / 만 루블
        가격이 0이면 계산하지 않습니다.
        """
        if not self.price:
            return None
        benefit = (self.ergonomics or 0) - (self.recoil_modifier or 0) * 100
        if benefit <= 0:
            return None
        return round(benefit / (self.price / 10000), 2)


class SlotOption(models.Model):
    """
    "총기 A의 '총구' 슬롯에는 부품 B를 끼울 수 있다"
    깊이 1단계만 저장합니다. (재귀 전체를 저장하면 데이터가 폭발합니다)
    """

    weapon = models.ForeignKey(
        Weapon, on_delete=models.CASCADE, related_name="slot_options"
    )
    slot_name = models.CharField("슬롯 이름", max_length=120, db_index=True)
    slot_order = models.PositiveSmallIntegerField("슬롯 순서", default=0)
    mod = models.ForeignKey(Mod, on_delete=models.CASCADE, related_name="fits_slots")

    class Meta:
        verbose_name = "슬롯 장착 옵션"
        verbose_name_plural = "슬롯 장착 옵션"
        # 같은 조합이 중복 저장되지 않도록 막습니다
        unique_together = [("weapon", "slot_name", "mod")]
        indexes = [models.Index(fields=["weapon", "slot_order"])]

    def __str__(self):
        return f"{self.weapon.name} / {self.slot_name} / {self.mod.name}"
