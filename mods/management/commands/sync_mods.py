"""
총기 / 프리셋 / 부품 데이터를 내려받아 저장합니다.

사용법:
    python manage.py sync_mods                   # 전체 동기화
    python manage.py sync_mods --lang en         # 영어 이름
    python manage.py sync_mods --mode pve        # PVE 가격
    python manage.py sync_mods --no-slots        # 슬롯 연결 생략 (빠름)
    python manage.py sync_mods --file items.json # 저장해둔 파일에서 읽기

⚠️ 설계 노트
json.tarkov.dev 의 정확한 필드명이 패치로 바뀔 수 있어서,
아래 pick() 함수로 '후보 이름을 여러 개 시도'하는 방식으로 짰습니다.
그래도 못 찾으면 조용히 실패하지 않고 경고를 출력합니다.
"""
import json

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from mods.models import Mod, Preset, SlotOption, Weapon

BASE_URL = "https://json.tarkov.dev"


def pick(data, *keys, default=None):
    """
    딕셔너리에서 여러 후보 키를 순서대로 찾아 첫 번째로 존재하는 값을 반환합니다.
    API 필드명이 조금 달라져도 코드가 버티도록 하는 안전장치입니다.
    """
    if not isinstance(data, dict):
        return default
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return default


def as_id(value):
    """
    참조가 문자열 ID로 올 수도 있고 {"id": "..."} 객체로 올 수도 있어서
    어느 쪽이든 ID 문자열로 통일합니다.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return pick(value, "id", "_id")
    return None


def as_name(value):
    """참조 객체에서 이름을 꺼냅니다. 문자열만 왔으면 None."""
    if isinstance(value, dict):
        return pick(value, "name", "shortName")
    return None


class Command(BaseCommand):
    help = "총기/프리셋/부품 데이터를 json.tarkov.dev 에서 동기화합니다."

    def add_arguments(self, parser):
        parser.add_argument("--lang", default="ko", help="언어 코드 (기본 ko)")
        parser.add_argument("--mode", default="regular",
                            choices=["regular", "pve", "pvp-season"],
                            help="게임 모드 (기본 regular)")
        parser.add_argument("--no-slots", action="store_true",
                            help="슬롯 장착 옵션 저장을 생략합니다 (훨씬 빠름)")
        parser.add_argument("--file", default=None,
                            help="네트워크 대신 로컬 JSON 파일에서 읽기")

    # ------------------------------------------------------------------
    def handle(self, *args, **opts):
        items = self.load_items(opts)
        if items is None:
            return

        self.stdout.write(f"아이템 {len(items)}개 로드 완료")

        # 이름 채우기. en 도 반드시 거쳐야 합니다 (위 apply_translation 주석 참고)
        if not opts["file"]:
            self.apply_translation(items, opts["lang"], opts["mode"])

        # 타입별로 분류
        guns, presets, mods = [], [], []
        for it in items:
            types = it.get("types") or []
            if "preset" in types:
                presets.append(it)
            elif "gun" in types:
                guns.append(it)
            elif self.is_mod(types):
                mods.append(it)

        self.stdout.write(
            f"분류 결과 → 총기 {len(guns)} / 프리셋 {len(presets)} / 부품 {len(mods)}"
        )
        if not guns:
            self.stderr.write(self.style.ERROR(
                "총기를 하나도 못 찾았습니다. types 필드명이 바뀌었을 수 있습니다."
            ))
            return

        # 한 번의 트랜잭션으로 묶으면 훨씬 빠르고, 중간에 실패해도 안전합니다
        with transaction.atomic():
            weapon_map = self.save_weapons(guns)
            mod_map = self.save_mods(mods)
            self.save_presets(presets, weapon_map)

            if opts["no_slots"]:
                self.stdout.write("슬롯 연결은 건너뜁니다 (--no-slots)")
            else:
                self.save_slot_options(guns, weapon_map, mod_map)

        self.stdout.write(self.style.SUCCESS("\n동기화 완료!"))
        self.stdout.write(
            f"  총기 {Weapon.objects.count()} · "
            f"프리셋 {Preset.objects.count()} · "
            f"부품 {Mod.objects.count()} · "
            f"슬롯옵션 {SlotOption.objects.count()}"
        )

    # ------------------------------------------------------------------
    def load_items(self, opts):
        """네트워크 또는 파일에서 아이템 배열을 가져옵니다."""
        if opts["file"]:
            self.stdout.write(f"파일에서 읽는 중: {opts['file']}")
            try:
                with open(opts["file"], encoding="utf-8") as f:
                    doc = json.load(f)
            except OSError as e:
                self.stderr.write(self.style.ERROR(f"파일 오류: {e}"))
                return None
        else:
            url = f"{BASE_URL}/{opts['mode']}/items"
            self.stdout.write(f"내려받는 중: {url} (수 MB, 시간이 좀 걸립니다)")
            try:
                res = requests.get(url, timeout=180)
                res.raise_for_status()
                doc = res.json()
            except requests.RequestException as e:
                self.stderr.write(self.style.ERROR(f"네트워크 오류: {e}"))
                return None
            except ValueError as e:
                self.stderr.write(self.style.ERROR(f"JSON 파싱 실패: {e}"))
                return None

        return self.extract_items(doc)

    def extract_items(self, doc):
        """
        응답 구조가 조금씩 달라도 아이템 목록을 찾아냅니다.

        ⚠️ 실제 json.tarkov.dev 는 data.items 를 '배열'이 아니라
           id를 키로 쓴 딕셔너리로 줍니다. 그래서 값만 뽑아 리스트로 만듭니다.
        """
        if isinstance(doc, list):
            return doc
        for path in (("items",), ("data", "items")):
            node = doc
            for part in path:
                node = node.get(part) if isinstance(node, dict) else None
            if isinstance(node, dict):
                node = list(node.values())
            if isinstance(node, list) and node:
                return node
        self.stderr.write(self.style.ERROR(
            f"아이템 목록을 못 찾았습니다. 최상위 키: {list(doc)[:15]}"
        ))
        return None

    def apply_translation(self, items, lang, mode):
        """
        이름 문서를 받아 실제 이름을 채웁니다.

        ⚠️ 이건 '번역'이라기보다 필수 과정입니다.
           기본 문서의 name 은 실제 이름이 아니라 "<id> Name" 형태의 '열쇠'라서,
           이 단계를 건너뛰면 화면에 "5447a9cd... Name" 이 그대로 찍힙니다.
           그래서 영어(en)도 items_en 을 받아야 합니다.

        번역 문서는 {"data": {"<id> Name": "실제이름", ...}} 형태의 평평한 딕셔너리입니다.
        """
        url = f"{BASE_URL}/{mode}/items_{lang}"
        self.stdout.write(f"이름 문서 요청: {url}")
        try:
            res = requests.get(url, timeout=180)
            res.raise_for_status()
            doc = res.json()
        except (requests.RequestException, ValueError) as e:
            self.stdout.write(self.style.WARNING(f"  실패({e}) → 이름이 ID로 표시됩니다"))
            return

        locale = doc.get("data") if isinstance(doc, dict) else None
        if not isinstance(locale, dict) or not locale:
            self.stdout.write(self.style.WARNING("  이름 매핑 실패 → 이름이 ID로 표시됩니다"))
            return

        hit, slot_hit = 0, 0
        for it in items:
            name = locale.get(it.get("name"))
            if name:
                it["name"] = name
                hit += 1
            short = locale.get(it.get("shortName"))
            if short:
                it["shortName"] = short

            # 슬롯 이름도 열쇠입니다. 안 바꾸면 화면에 MOD_MUZZLE 이 그대로 찍힙니다.
            for slot in (it.get("properties") or {}).get("slots") or []:
                sname = locale.get(slot.get("name"))
                if sname:
                    slot["name"] = sname
                    slot_hit += 1

        self.stdout.write(f"  이름 적용 {hit}개 (슬롯 이름 {slot_hit}개)")

    @staticmethod
    def is_mod(types):
        """부품으로 취급할 타입들"""
        mod_types = {
            "mods", "suppressor", "pistolGrip", "barrel", "handguard",
            "stock", "scope", "sights", "magazine", "muzzle", "foregrip",
        }
        return bool(mod_types & set(types))

    # ------------------------------------------------------------------
    def save_weapons(self, guns):
        """총기 저장. 반환값은 {api_id: Weapon} 딕셔너리"""
        objs = []
        for g in guns:
            p = g.get("properties") or {}
            objs.append(Weapon(
                api_id=pick(g, "id", "_id"),
                name=pick(g, "name", default="?"),
                short_name=pick(g, "shortName", default="") or "",
                icon_link=pick(g, "iconLink", "gridImageLink", default="") or "",
                wiki_link=pick(g, "wikiLink", default="") or "",
                caliber=pick(p, "caliber", default="") or "",
                ergonomics=pick(p, "ergonomics", "defaultErgonomics"),
                recoil_vertical=pick(p, "recoilVertical", "defaultRecoilVertical"),
                recoil_horizontal=pick(p, "recoilHorizontal", "defaultRecoilHorizontal"),
                fire_rate=pick(p, "fireRate"),
                price=pick(g, "avg24hPrice", "basePrice", default=0) or 0,
                slots_raw=pick(p, "slots", default=[]) or [],
            ))
        Weapon.objects.all().delete()
        Weapon.objects.bulk_create(objs, batch_size=500)
        self.stdout.write(f"  총기 {len(objs)}개 저장")
        return {w.api_id: w for w in objs}

    def save_mods(self, mods):
        """부품 저장. 반환값은 {api_id: Mod} 딕셔너리"""
        objs = []
        for m in mods:
            p = m.get("properties") or {}
            types = m.get("types") or []
            objs.append(Mod(
                api_id=pick(m, "id", "_id"),
                name=pick(m, "name", default="?"),
                short_name=pick(m, "shortName", default="") or "",
                icon_link=pick(m, "iconLink", "gridImageLink", default="") or "",
                wiki_link=pick(m, "wikiLink", default="") or "",
                mod_type=next((t for t in types if t != "mods"), "mods"),
                # 최상위에 있을 수도, properties 안에 있을 수도 있어 둘 다 확인
                ergonomics=pick(p, "ergonomics") or pick(m, "ergonomicsModifier"),
                recoil_modifier=pick(p, "recoilModifier") or pick(m, "recoilModifier"),
                accuracy_modifier=pick(p, "accuracyModifier") or pick(m, "accuracyModifier"),
                price=pick(m, "avg24hPrice", "basePrice", default=0) or 0,
                slots_raw=pick(p, "slots", default=[]) or [],
            ))
        Mod.objects.all().delete()
        Mod.objects.bulk_create(objs, batch_size=500)
        self.stdout.write(f"  부품 {len(objs)}개 저장")
        return {m.api_id: m for m in objs}

    def save_presets(self, presets, weapon_map):
        """프리셋 저장 (1단계의 핵심 데이터)"""
        objs = []
        for pr in presets:
            p = pr.get("properties") or {}
            base = pick(p, "baseItem", "base")
            base_id = as_id(base)
            objs.append(Preset(
                api_id=pick(pr, "id", "_id"),
                name=pick(pr, "name", default="?"),
                base_weapon=weapon_map.get(base_id),
                base_name=as_name(base) or (
                    weapon_map[base_id].name if base_id in weapon_map else ""
                ),
                icon_link=pick(pr, "iconLink", "gridImageLink", default="") or "",
                wiki_link=pick(pr, "wikiLink", default="") or "",
                ergonomics=pick(p, "ergonomics"),
                recoil_vertical=pick(p, "recoilVertical"),
                recoil_horizontal=pick(p, "recoilHorizontal"),
                moa=pick(p, "moa"),
                is_default=bool(pick(p, "default", default=False)),
                price=pick(pr, "avg24hPrice", "basePrice", default=0) or 0,
            ))
        Preset.objects.all().delete()
        Preset.objects.bulk_create(objs, batch_size=500)

        linked = sum(1 for o in objs if o.base_weapon_id)
        self.stdout.write(f"  프리셋 {len(objs)}개 저장 (총기 연결 {linked}개)")
        if objs and linked == 0:
            self.stdout.write(self.style.WARNING(
                "    ⚠️ baseItem 연결이 하나도 안 됐습니다. 필드명 확인이 필요합니다."
            ))

    def save_slot_options(self, guns, weapon_map, mod_map):
        """
        2단계: 총기 슬롯 ↔ 장착 가능 부품 연결.
        깊이 1단계만 저장합니다.
        """
        options = []
        seen = set()          # 중복 방지용
        missing_mod = 0       # 부품 목록에 없던 참조 개수

        for g in guns:
            gid = pick(g, "id", "_id")
            weapon = weapon_map.get(gid)
            if not weapon:
                continue

            slots = pick(g.get("properties") or {}, "slots", default=[]) or []
            for order, slot in enumerate(slots):
                slot_name = pick(slot, "name", "nameId", default=f"슬롯{order+1}")
                filters = pick(slot, "filters", default={}) or {}
                allowed = pick(filters, "allowedItems", "allowedItemIds", default=[]) or []

                for ref in allowed:
                    mid = as_id(ref)
                    mod = mod_map.get(mid)
                    if not mod:
                        missing_mod += 1
                        continue
                    key = (gid, slot_name, mid)
                    if key in seen:
                        continue
                    seen.add(key)
                    options.append(SlotOption(
                        weapon=weapon, slot_name=slot_name,
                        slot_order=order, mod=mod,
                    ))

        SlotOption.objects.all().delete()
        SlotOption.objects.bulk_create(options, batch_size=2000)
        self.stdout.write(f"  슬롯 옵션 {len(options)}개 저장")

        if missing_mod:
            self.stdout.write(self.style.WARNING(
                f"    참고: 부품 목록에 없는 참조 {missing_mod}건은 건너뛰었습니다"
            ))
        if not options:
            self.stdout.write(self.style.WARNING(
                "    ⚠️ 슬롯 연결이 0건입니다. slots/filters 구조 확인이 필요합니다."
            ))
