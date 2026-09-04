"""모딩 페이지 뷰"""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Mod, Preset, SlotOption, Weapon


def index(request):
    """모딩 홈 — 3단계 안내와 데이터 현황"""
    return render(request, "mods/index.html", {
        "weapon_count": Weapon.objects.count(),
        "preset_count": Preset.objects.count(),
        "mod_count": Mod.objects.count(),
        "slot_count": SlotOption.objects.count(),
    })


# ---------------------------------------------------------------- 1단계
def presets(request):
    """
    완성 프리셋 비교.
    같은 총끼리 묶어서 보여줘야 의미가 있으므로 기반 총기별로 그룹핑합니다.
    """
    keyword = request.GET.get("q", "").strip()

    qs = Preset.objects.select_related("base_weapon")
    if keyword:
        qs = qs.filter(Q(name__icontains=keyword) | Q(base_name__icontains=keyword))

    # 기반 총기명으로 묶기
    groups = {}
    for p in qs:
        key = p.base_name or "(기반 총기 정보 없음)"
        groups.setdefault(key, []).append(p)

    # 각 그룹 안에서는 종합 점수가 높은 순
    grouped = []
    for base, plist in sorted(groups.items()):
        plist.sort(key=lambda x: x.score, reverse=True)
        grouped.append({"base": base, "presets": plist, "best": plist[0]})

    # 프리셋이 여러 개인 총기를 먼저 보여줍니다 (비교할 게 있어야 유용하므로)
    grouped.sort(key=lambda g: len(g["presets"]), reverse=True)

    return render(request, "mods/presets.html", {
        "grouped": grouped, "keyword": keyword,
    })


# ---------------------------------------------------------------- 2단계
def weapons(request):
    """총기 목록 — 슬롯이 많은 순 (모딩 여지가 큰 총)"""
    keyword = request.GET.get("q", "").strip()

    qs = Weapon.objects.all()
    if keyword:
        qs = qs.filter(Q(name__icontains=keyword) | Q(caliber__icontains=keyword))

    # 슬롯 옵션이 실제로 몇 개 연결됐는지 함께 세어옵니다
    qs = qs.annotate(option_count=Count("slot_options"))
    items = sorted(qs, key=lambda w: w.option_count, reverse=True)

    return render(request, "mods/weapons.html", {
        "weapons": items, "keyword": keyword,
    })


def weapon_detail(request, api_id):
    """
    총기 1정의 슬롯 트리 (깊이 1단계).

    ⚠️ 슬롯 하나에 장착 가능한 부품이 수십~수백 개라
    전부 뿌리면 브라우저가 멈춥니다. 슬롯당 상위 8개만 잘라서 보여줍니다.
    """
    weapon = get_object_or_404(Weapon, api_id=api_id)

    # 정렬 기준: 반동 감소(기본) 또는 조준편의
    sort_key = request.GET.get("sort", "recoil")

    options = (SlotOption.objects
               .filter(weapon=weapon)
               .select_related("mod")
               .order_by("slot_order"))

    # 슬롯 이름별로 묶기
    buckets = {}
    for opt in options:
        buckets.setdefault((opt.slot_order, opt.slot_name), []).append(opt.mod)

    slots = []
    for (order, name), mod_list in sorted(buckets.items()):
        total = len(mod_list)

        if sort_key == "ergo":
            # 조준편의는 높을수록 좋음
            mod_list.sort(key=lambda m: m.ergonomics or 0, reverse=True)
        else:
            # 반동 변화율은 낮을(음수일)수록 좋음
            mod_list.sort(key=lambda m: m.recoil_modifier if m.recoil_modifier is not None else 0)

        slots.append({
            "name": name,
            "total": total,
            "top": mod_list[:8],       # 상위 8개만
            "hidden": max(total - 8, 0),
        })

    return render(request, "mods/weapon_detail.html", {
        "weapon": weapon, "slots": slots, "sort_key": sort_key,
    })


# ---------------------------------------------------------------- 3단계
def parts(request):
    """부품 가성비 랭킹 — 예산 필터 포함"""
    sort_key = request.GET.get("sort", "value")
    budget = request.GET.get("budget", "")
    mod_type = request.GET.get("type", "")

    qs = Mod.objects.all()

    if mod_type:
        qs = qs.filter(mod_type=mod_type)

    # 예산 상한 (루블). 숫자가 아니면 무시합니다.
    if budget.isdigit():
        qs = qs.filter(price__lte=int(budget), price__gt=0)

    items = list(qs)

    if sort_key == "ergo":
        items.sort(key=lambda m: m.ergonomics or 0, reverse=True)
    elif sort_key == "recoil":
        items.sort(key=lambda m: m.recoil_modifier if m.recoil_modifier is not None else 0)
    else:
        # 가성비 순 — 점수가 없는 부품은 뒤로
        items.sort(key=lambda m: m.value_score or -1, reverse=True)

    types = (Mod.objects.exclude(mod_type="")
             .values_list("mod_type", flat=True).distinct().order_by("mod_type"))

    return render(request, "mods/parts.html", {
        "items": items[:120],          # 너무 길면 화면이 무거워집니다
        "total": len(items),
        "types": types,
        "sort_key": sort_key,
        "budget": budget,
        "mod_type": mod_type,
    })
