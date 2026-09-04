"""
데이터 모델 정의

설계 포인트:
아이템 종류(의료품/가방/탄약)마다 스펙 항목이 완전히 다릅니다.
테이블을 3개로 쪼개면 관리가 번거로우니, 공통 정보는 컬럼으로 두고
종류별 스펙은 JSONField(properties) 하나에 통째로 담았습니다.

비유하자면 — 서랍장의 공통 칸(이름/이미지/가격)은 정해두고,
물건마다 다른 잡동사니는 '만능 주머니' 하나에 넣어두는 방식입니다.
"""
from django.db import models

# API가 주는 구경 코드는 사람이 읽기 어렵습니다 (Caliber1143x23ACP).
# 번역표에도 없어서 여기서 직접 이름표를 붙입니다.
# 값은 (읽기 좋은 이름, 묶음) — 묶음은 화면의 선택 상자를 나누는 데 씁니다.
#
# 이름은 지어낸 게 아니라 실제 탄약 이름에서 그대로 가져왔습니다.
# 예: Caliber1143x23ACP 에 속한 탄이 ".45 ACP AP", ".45 ACP RIP" → ".45 ACP"
CALIBERS = {
    # --- 소총탄 ---
    "Caliber545x39": ("5.45x39mm", "소총"),
    "Caliber556x45NATO": ("5.56x45mm", "소총"),
    "Caliber762x39": ("7.62x39mm", "소총"),
    "Caliber762x51": ("7.62x51mm", "소총"),
    "Caliber762x54R": ("7.62x54mmR", "소총"),
    "Caliber762x35": (".300 Blackout", "소총"),
    "Caliber9x39": ("9x39mm", "소총"),
    "Caliber366TKM": (".366 TKM", "소총"),
    "Caliber58x42": ("5.8x42mm", "소총"),
    "Caliber68x51": ("6.8x51mm", "소총"),
    "Caliber784x49": (".308 ME", "소총"),
    # --- 저격/대물탄 ---
    "Caliber86x70": (".338 라푸아 매그넘", "저격"),
    "Caliber93x64": ("9.3x64mm", "저격"),
    "Caliber127x55": ("12.7x55mm", "저격"),
    "Caliber127x99": (".50 BMG", "저격"),
    # --- 권총 · 기관단총탄 ---
    "Caliber9x18PM": ("9x18mm PM", "권총·기관단총"),
    "Caliber9x19PARA": ("9x19mm 파라벨룸", "권총·기관단총"),
    "Caliber9x21": ("9x21mm", "권총·기관단총"),
    "Caliber762x25TT": ("7.62x25mm TT", "권총·기관단총"),
    "Caliber1143x23ACP": (".45 ACP", "권총·기관단총"),
    "Caliber9x33R": (".357 매그넘", "권총·기관단총"),
    "Caliber127x33": (".50 AE", "권총·기관단총"),
    "Caliber57x28": ("5.7x28mm", "권총·기관단총"),
    "Caliber46x30": ("4.6x30mm", "권총·기관단총"),
    # --- 산탄 ---
    "Caliber12g": ("12게이지 (12/70)", "산탄"),
    "Caliber20g": ("20게이지 (20/70)", "산탄"),
    "Caliber23x75": ("23x75mm (KS-23)", "산탄"),
    # --- 유탄 · 신호탄 ---
    "Caliber40x46": ("40x46mm 유탄", "유탄·신호탄"),
    "Caliber40mmRU": ("40mm VOG 유탄", "유탄·신호탄"),
    "Caliber26x75": ("26x75mm 신호탄", "유탄·신호탄"),
    "Caliber20x1mm": ("20x1mm 디스크", "유탄·신호탄"),
}

# 화면의 선택 상자에 나올 묶음 순서 (초보자가 자주 쓰는 것부터)
CALIBER_GROUPS = ["소총", "권총·기관단총", "산탄", "저격", "유탄·신호탄"]


class TarkovItem(models.Model):
    """tarkov.dev API에서 가져온 아이템 1개"""

    # --- 카테고리 구분용 상수 ---
    CATEGORY_CHOICES = [
        ("meds", "의료품 / 주사기"),
        ("backpack", "가방"),
        ("rig", "리그(체스트리그)"),
        ("ammo", "탄약"),
    ]

    # API가 주는 고유 ID를 그대로 기본키로 사용 → 재동기화 시 중복 방지
    api_id = models.CharField("API 고유 ID", max_length=64, primary_key=True)
    category = models.CharField(
        "분류", max_length=20, choices=CATEGORY_CHOICES, db_index=True
    )

    name = models.CharField("이름", max_length=255)
    short_name = models.CharField("축약 이름", max_length=100, blank=True)
    description = models.TextField("설명", blank=True)

    # --- 이미지 (URL만 저장하고 화면에서 불러옵니다) ---
    icon_link = models.URLField("아이콘 URL", max_length=500, blank=True)
    image_link = models.URLField("큰 이미지 URL", max_length=500, blank=True)
    wiki_link = models.URLField("위키 URL", max_length=500, blank=True)

    # --- 인벤토리에서 차지하는 칸 ---
    width = models.PositiveSmallIntegerField("가로 칸", default=1)
    height = models.PositiveSmallIntegerField("세로 칸", default=1)

    # --- 가격 ---
    base_price = models.IntegerField("기본가", default=0)
    avg_24h_price = models.IntegerField("24시간 평균가", null=True, blank=True)

    # --- 종류별 상세 스펙 (딕셔너리 통째로 저장) ---
    properties = models.JSONField("상세 스펙", default=dict, blank=True)

    synced_at = models.DateTimeField("동기화 시각", auto_now=True)

    class Meta:
        verbose_name = "타르코프 아이템"
        verbose_name_plural = "타르코프 아이템"
        ordering = ["name"]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"

    # ---------- 템플릿에서 쓰기 편하도록 만든 도우미들 ----------

    @property
    def slots(self):
        """인벤토리에서 차지하는 총 칸 수 (예: 2x3 = 6칸)"""
        return self.width * self.height

    @property
    def price_per_slot(self):
        """칸당 가격 — 가방/리그 가성비 비교에 씁니다."""
        price = self.avg_24h_price or self.base_price
        capacity = self.properties.get("capacity") or 0
        if not capacity:
            return None
        return round(price / capacity)

    @property
    def caliber_kr(self):
        """구경 코드를 읽기 좋은 이름으로. 모르는 코드면 'Caliber'만 떼고 보여줍니다."""
        code = self.properties.get("caliber")
        if not code:
            return ""
        name, _ = CALIBERS.get(code, (code.removeprefix("Caliber"), ""))
        return name

    @property
    def is_injector(self):
        """주사기인지 (알약·붕대류와 구분)"""
        return bool(self.properties.get("injector"))

    @property
    def cures_kr(self):
        """치료 가능한 상태를 한글로 변환"""
        table = {
            "LightBleeding": "경상 출혈",
            "HeavyBleeding": "중상 출혈",
            "Fracture": "골절",
            "Contusion": "뇌진탕",
            "Pain": "통증",
            "Dehydration": "탈수",
            "Exhaustion": "탈진",
            "RadExposure": "방사능",
            "Intoxication": "중독",
            "Tremor": "손떨림",
        }
        cures = self.properties.get("cures") or []
        return [table.get(c, c) for c in cures]

    @property
    def grid_cells(self):
        """
        가방/리그 내부 수납 칸의 '실제 격자 모양'을 화면에 그리기 위한 데이터입니다.

        Django 템플릿에는 "N번 반복" 문법이 없어서,
        파이썬에서 미리 칸 개수만큼의 리스트를 만들어 넘겨줍니다.
        """
        grids = self.properties.get("grids") or []
        result = []
        for g in grids:
            w = g.get("width") or 1
            h = g.get("height") or 1
            result.append({
                "w": w,
                "h": h,
                "cells": range(w * h),  # 템플릿에서 {% for _ in grid.cells %} 로 사용
            })
        return result

    @property
    def pen_grade(self):
        """
        관통력(penetrationPower)을 초보자용 5단계 등급으로 변환합니다.
        타르코프 방탄 등급 체계에 대략 맞춰 나눈 값입니다.
        """
        pen = self.properties.get("penetrationPower")
        if pen is None:
            return ("정보없음", "gray")
        if pen >= 50:
            return ("클래스 6 관통 가능", "purple")
        if pen >= 40:
            return ("클래스 5 관통 가능", "red")
        if pen >= 30:
            return ("클래스 4 관통 가능", "orange")
        if pen >= 20:
            return ("클래스 3 관통 가능", "yellow")
        return ("저관통 (방탄에 매우 약함)", "gray")
