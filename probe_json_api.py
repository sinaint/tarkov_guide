r"""
json.tarkov.dev 의 실제 응답 구조를 확인하는 조사용 스크립트입니다.

이 파일은 Django와 무관하게 단독으로 돌아갑니다.
프로젝트 폴더에 넣고 아래처럼 실행해 주세요.

    .venv\Scripts\python.exe probe_json_api.py

출력된 내용을 그대로 복사해서 알려주시면
sync_tarkov.py 를 정확한 필드명으로 다시 만들어 드리겠습니다.
"""
import json

import requests

BASE = "https://json.tarkov.dev"

# 아이템 JSON은 수 MB 단위로 큽니다. 다운로드에 시간이 걸릴 수 있어요.
TIMEOUT = 120


def show(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def get_json(url):
    """URL을 호출해 JSON을 반환합니다. 실패하면 이유를 출력하고 None."""
    print(f"\n요청 → {url}")
    try:
        res = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"  ✗ 네트워크 오류: {e}")
        return None

    size_mb = len(res.content) / 1024 / 1024
    print(f"  상태코드 {res.status_code} · 크기 {size_mb:.2f} MB")

    if res.status_code != 200:
        print(f"  본문 앞부분: {res.text[:300]}")
        return None

    try:
        return res.json()
    except ValueError:
        print(f"  ✗ JSON 파싱 실패. 본문 앞부분: {res.text[:300]}")
        return None


def preview(obj, depth=0):
    """중첩된 딕셔너리/리스트의 '모양'만 간단히 출력합니다."""
    pad = "  " * depth
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:25]:
            kind = type(v).__name__
            if isinstance(v, (dict, list)):
                n = len(v)
                print(f"{pad}- {k}: {kind}({n}개)")
            else:
                # 값이 길면 잘라서 표시
                s = str(v)
                print(f"{pad}- {k}: {kind} = {s[:60]}")
    elif isinstance(obj, list):
        print(f"{pad}(리스트 {len(obj)}개)")


def main():
    # ---------- 1. 엔드포인트 목록 ----------
    show("1. 사용 가능한 엔드포인트")
    data = get_json(f"{BASE}/endpoints")
    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])

    # ---------- 2. 영어 기준 아이템 데이터 ----------
    show("2. items (영어 기준) 최상위 구조")
    items_doc = get_json(f"{BASE}/regular/items")
    if not items_doc:
        print("아이템 데이터를 못 받았습니다. 여기서 중단합니다.")
        return

    print("\n[최상위 키]")
    preview(items_doc)

    # 실제 아이템 배열이 어디 들어있는지 찾아봅니다
    items = None
    for path in ("items", "data.items"):
        node = items_doc
        for part in path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        # 실제 응답은 id를 키로 쓴 dict 입니다. 리스트 형태도 받아둡니다.
        if isinstance(node, dict):
            node = list(node.values())
        if isinstance(node, list) and node:
            items = node
            print(f"\n→ 아이템 배열 위치: '{path}' ({len(items)}개)")
            break

    if not items:
        print("\n⚠️ 아이템 배열을 자동으로 못 찾았습니다. 위 최상위 키 목록을 알려주세요.")
        return

    # ---------- 3. 아이템 1개의 전체 필드 ----------
    show("3. 아이템 샘플 1개 (전체 필드)")
    print(json.dumps(items[0], ensure_ascii=False, indent=2)[:2500])

    # ---------- 4. 우리가 필요한 카테고리 샘플 ----------
    show("4. 탄약 / 가방 / 의료품 샘플")

    def find_by_type(keyword):
        """types 배열에 특정 값이 든 아이템을 하나 찾습니다."""
        for it in items:
            types = it.get("types") or []
            if keyword in types:
                return it
        return None

    for kind in ("ammo", "backpack", "rig", "meds"):
        sample = find_by_type(kind)
        print(f"\n--- {kind} ---")
        if sample:
            print(f"이름: {sample.get('name')}")
            print("properties 내용:")
            print(json.dumps(sample.get("properties"), ensure_ascii=False, indent=2)[:900])
        else:
            print("해당 타입을 못 찾았습니다 (types 필드명이 다를 수 있음)")

    # ---------- 5. 한국어 번역 문서 ----------
    show("5. 한국어 번역 문서 구조")
    ko = get_json(f"{BASE}/regular/items_ko")
    if ko:
        print("\n[최상위 키]")
        preview(ko)
        print("\n[샘플 앞부분]")
        print(json.dumps(ko, ensure_ascii=False, indent=2)[:1200])

    show("완료")
    print("위 출력 전체를 복사해서 알려주세요!")


if __name__ == "__main__":
    main()
