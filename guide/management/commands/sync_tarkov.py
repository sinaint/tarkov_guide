"""
tarkov.dev 데이터를 내려받아 DB에 저장하는 명령어입니다.

사용법:
    python manage.py sync_tarkov              # 전체 동기화 (한국어)
    python manage.py sync_tarkov --lang en    # 영어 이름으로
    python manage.py sync_tarkov --only ammo  # 탄약만
    python manage.py sync_tarkov --mode pve   # PVE 모드 가격 기준
    python manage.py sync_tarkov --force      # 변경이 없어도 강제로 다시 저장

원본 데이터는 하루 한두 번 갱신됩니다. 이 명령어는 서버가 준 ETag를 기억해 두고
다음 실행 때 "그때 그대로냐?"고 먼저 물어봅니다. 그대로면 서버가 304(내용 없음)만
돌려주므로 16MB를 다시 받지 않고 즉시 끝납니다. 그래서 1시간마다 돌려도 부담이 없고,
갱신되는 순간 바로 따라잡습니다. (자동 실행 등록 방법은 README 참고)
"""
import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from guide.models import TarkovItem

BASE = "https://json.tarkov.dev"

# 서버가 준 ETag를 적어두는 파일. 지우면 다음 실행 때 전체를 다시 받습니다.
ETAG_FILE = settings.BASE_DIR / ".sync_etag.json"

# 아이템의 properties.propertiesType → 우리 DB 카테고리
#
# ⚠️ types 배열로 나누면 안 됩니다. 예를 들어 수류탄도 types에 "ammo"가 들어 있어서
#    탄약 페이지에 섞여 버립니다. propertiesType은 스펙 구조 그 자체라 정확합니다.
PROPS_TO_CATEGORY = {
    "ItemPropertiesAmmo": "ammo",
    "ItemPropertiesBackpack": "backpack",
    "ItemPropertiesChestRig": "rig",
    "ItemPropertiesMedKit": "meds",
    "ItemPropertiesMedicalItem": "meds",
    "ItemPropertiesPainkiller": "meds",
    "ItemPropertiesSurgicalKit": "meds",
    "ItemPropertiesStim": "meds",
}


class Command(BaseCommand):
    help = "tarkov.dev에서 의료품/가방/리그/탄약 데이터를 동기화합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lang", default="ko",
            help="아이템 이름 언어 (ko, en, ja, ru 등). 기본값: ko",
        )
        parser.add_argument(
            "--mode", default="regular", choices=["regular", "pve"],
            help="게임 모드. regular(PVP) 또는 pve. 기본값: regular",
        )
        parser.add_argument(
            "--only", default=None,
            help="특정 카테고리만 동기화 (ammo, backpack, rig, meds)",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="원본이 그대로여도 건너뛰지 않고 다시 저장합니다",
        )

    def handle(self, *args, **options):
        lang, mode = options["lang"], options["mode"]
        only, force = options["only"], options["force"]

        if only and only not in set(PROPS_TO_CATEGORY.values()):
            self.stderr.write(self.style.ERROR(f"알 수 없는 카테고리: {only}"))
            return

        cache = self.load_etags()

        try:
            items_doc, items_etag = self.fetch(f"{mode}/items", cache, force)
            names, names_etag = self.fetch(f"{mode}/items_{lang}", cache, force)
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"네트워크 오류: {e}"))
            return
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"응답 형식 오류: {e}"))
            return

        # 둘 다 304면 받을 게 없습니다.
        if items_doc is None and names is None:
            self.stdout.write("원본이 그대로입니다. 갱신할 내용이 없습니다.")
            return

        # 둘 중 하나만 바뀐 경우, 안 바뀐 쪽은 캐시가 아니라 다시 받아야 합니다.
        # (양이 적고 드문 상황이라 그냥 강제로 한 번 더 받습니다.)
        if items_doc is None:
            items_doc, items_etag = self.fetch(f"{mode}/items", cache, force=True)
        if names is None:
            names, names_etag = self.fetch(f"{mode}/items_{lang}", cache, force=True)

        raw_items = (items_doc.get("data") or {}).get("items")
        if not isinstance(raw_items, dict):
            self.stderr.write(self.style.ERROR("data.items 를 찾지 못했습니다."))
            return

        # 번역 문서는 "<id> Name" → "실제 이름" 형태의 평평한 딕셔너리입니다.
        locale = names.get("data") or {}

        self.stdout.write(f"{len(raw_items)}개 수신. DB에 저장합니다...")
        created, updated, seen = 0, 0, set()

        for raw in raw_items.values():
            props = raw.get("properties") or {}
            category = PROPS_TO_CATEGORY.get(props.get("propertiesType"))
            if category is None or (only and category != only):
                continue

            _, is_created = TarkovItem.objects.update_or_create(
                api_id=raw["id"],
                defaults={
                    "category": category,
                    # 기본 문서의 name은 실제 이름이 아니라 번역표를 찾는 '열쇠'입니다.
                    "name": locale.get(raw.get("name")) or raw.get("name") or "",
                    "short_name": locale.get(raw.get("shortName")) or "",
                    "description": locale.get(raw.get("description")) or "",
                    "icon_link": raw.get("iconLink") or "",
                    "image_link": raw.get("image512pxLink") or "",
                    "wiki_link": raw.get("wikiLink") or "",
                    "width": raw.get("width") or 1,
                    "height": raw.get("height") or 1,
                    "base_price": raw.get("basePrice") or 0,
                    "avg_24h_price": raw.get("avg24hPrice"),
                    "properties": self.slim(props, locale, raw.get("types") or []),
                },
            )
            seen.add(raw["id"])
            created += is_created
            updated += not is_created

        # 원본에서 사라진 아이템(과 seed_demo가 넣어둔 가짜 데이터)을 정리합니다.
        stale = TarkovItem.objects.exclude(api_id__in=seen)
        if only:
            stale = stale.filter(category=only)
        removed = stale.delete()[0]

        self.save_etags(cache, {f"{mode}/items": items_etag,
                                f"{mode}/items_{lang}": names_etag})

        self.stdout.write(self.style.SUCCESS(
            f"완료! 신규 {created}개 / 갱신 {updated}개 / 삭제 {removed}개"
        ))

    # ---------- 내려받기 ----------

    def fetch(self, path, cache, force):
        """
        (문서, ETag)를 반환합니다. 서버가 304를 주면 문서 자리에 None이 옵니다.
        """
        url = f"{BASE}/{path}"
        headers = {}
        if not force and cache.get(path):
            headers["If-None-Match"] = cache[path]

        self.stdout.write(f"요청 중... {url}")
        res = requests.get(url, headers=headers, timeout=180)

        if res.status_code == 304:
            self.stdout.write("  → 변경 없음 (304)")
            return None, cache.get(path)

        res.raise_for_status()
        self.stdout.write(f"  → {len(res.content) / 1024 / 1024:.1f} MB 수신")
        return res.json(), res.headers.get("ETag")

    # ---------- ETag 기억해 두기 ----------

    @staticmethod
    def load_etags():
        try:
            return json.loads(ETAG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # 파일이 없거나 깨졌으면 그냥 처음부터 받습니다.
            return {}

    @staticmethod
    def save_etags(cache, new):
        cache.update({k: v for k, v in new.items() if v})
        ETAG_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    # ---------- 저장 전 다이어트 ----------

    @staticmethod
    def slim(props, locale, types=()):
        """
        저장 전 손질:
          1. grids 안에는 '이 칸에 넣을 수 있는 아이템 ID 목록'(filters)이 통째로 들어 있어
             아이템 하나가 수십 KB까지 커집니다. 화면에서 쓰는 건 가로/세로뿐이라 잘라냅니다.
          2. 주사기 효과 이름(type/skill)도 번역표를 거쳐야 하는 '열쇠'입니다.
             예: "BodyTemperature" → "체온", "Attention" → "주의력"
        """
        props = {k: v for k, v in props.items() if k not in ("propertiesType", "locale")}

        if isinstance(props.get("grids"), list):
            props["grids"] = [
                {"width": g.get("width") or 1, "height": g.get("height") or 1}
                for g in props["grids"]
            ]

        if isinstance(props.get("stimEffects"), list):
            props["stimEffects"] = [
                {**e,
                 "type": locale.get(e.get("type")) or e.get("type"),
                 "skill": locale.get(e.get("skill")) or e.get("skill")}
                for e in props["stimEffects"]
            ]

        # 의료품 안에서 '주사기'만 따로 보여주기 위한 표시입니다.
        # (알약인 진통제와 주사제를 propertiesType으로는 구분할 수 없어 types를 씁니다)
        #
        # ⚠️ True일 때만 넣으면 안 됩니다. JSONField 에서 키가 없는 행은 SQL상 NULL이라
        #    exclude(injector=True) 에 걸러지지 않고 통째로 사라집니다. 항상 넣습니다.
        if "meds" in types or "injectors" in types:
            props["injector"] = "injectors" in types

        return props
