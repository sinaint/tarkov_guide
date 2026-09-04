"""화면(View) 로직"""
from django.db.models import Count
from django.shortcuts import render

from .models import CALIBER_GROUPS, CALIBERS, TarkovItem


def index(request):
    """홈: 카테고리별 개수 요약"""
    counts = {
        row["category"]: row["n"]
        for row in TarkovItem.objects.values("category").annotate(n=Count("api_id"))
    }
    return render(request, "guide/index.html", {"counts": counts})


def meds(request):
    """의료품 / 주사기 목록"""
    keyword = request.GET.get("q", "").strip()

    kind = request.GET.get("kind", "")
    if kind not in ("med", "injector"):
        kind = ""  # 빈 값 = 전체

    items = TarkovItem.objects.filter(category="meds")
    if keyword:
        items = items.filter(name__icontains=keyword)
    if kind:
        # 주사기 여부는 properties 안에 표시해 두었습니다 (sync_tarkov 참고)
        items = items.filter(properties__injector=(kind == "injector"))

    # 가격이 싼 순으로 = 초보자가 먼저 접하는 순서
    items = sorted(items, key=lambda i: i.avg_24h_price or i.base_price or 0)

    return render(request, "guide/meds.html",
                  {"items": items, "keyword": keyword, "kind": kind})


def storage(request):
    """가방 / 리그 목록 — 칸 수와 격자 모양을 함께 보여줍니다."""
    kind = request.GET.get("kind", "backpack")
    if kind not in ("backpack", "rig"):
        kind = "backpack"

    items = list(TarkovItem.objects.filter(category=kind))
    # 수납 칸 수가 많은 순 정렬 (capacity 가 없으면 0으로 처리)
    items.sort(key=lambda i: i.properties.get("capacity") or 0, reverse=True)

    return render(request, "guide/storage.html", {"items": items, "kind": kind})


def ammo(request):
    """탄약 목록 — 구경별로 묶어서 피해량/관통력 비교"""
    items = list(TarkovItem.objects.filter(category="ammo"))

    # 선택 상자에 넣을 구경 목록을 '소총 / 권총 / 산탄 …' 묶음별로 정리합니다.
    # 31개를 네모 버튼으로 늘어놓으면 눈에 안 들어와서 묶어 놓았습니다.
    codes = {i.properties.get("caliber") for i in items}
    codes.discard(None)
    groups = []
    for group in CALIBER_GROUPS:
        members = sorted(
            ((c, CALIBERS[c][0]) for c in codes if CALIBERS.get(c, ("", ""))[1] == group),
            key=lambda pair: pair[1],
        )
        if members:
            groups.append((group, members))
    # 표에 없는 새 구경이 생겨도 빠뜨리지 않도록 마지막에 모아둡니다.
    etc = sorted((c, c.removeprefix("Caliber")) for c in codes if c not in CALIBERS)
    if etc:
        groups.append(("기타", etc))

    selected = request.GET.get("caliber", "")
    if selected:
        items = [i for i in items if i.properties.get("caliber") == selected]

    # 정렬 기준: 관통력(기본) 또는 피해량
    sort_key = request.GET.get("sort", "pen")
    field = "damage" if sort_key == "damage" else "penetrationPower"
    items.sort(key=lambda i: i.properties.get(field) or 0, reverse=True)

    return render(request, "guide/ammo.html", {
        "items": items,
        "caliber_groups": groups,
        "selected": selected,
        "sort_key": sort_key,
    })
