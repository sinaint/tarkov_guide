# 총기 모딩 앱 설치 안내

기존 `guide` 앱은 **한 줄도 수정하지 않습니다.**
완성하신 `sync_tarkov.py`가 어떤 모양이든 그대로 두셔도 됩니다.

---

## 1단계. 폴더 복사

압축을 풀어 나온 `mods` 폴더를 `manage.py`가 있는 위치에 통째로 넣어주세요.

```
tarkov_guide/
├─ manage.py
├─ config/
├─ guide/        ← 기존 (건드리지 않음)
└─ mods/         ← ★ 새로 추가
```

## 2단계. 앱 등록 — `config/settings.py`

`INSTALLED_APPS` 목록에 한 줄 추가합니다.

```python
INSTALLED_APPS = [
    ...
    "guide",
    "mods",   # ← 이 줄 추가
]
```

## 3단계. 주소 연결 — `config/urls.py`

⚠️ **순서가 중요합니다.** `guide.urls`가 빈 경로(`""`)를 잡고 있으므로 반드시 그 **위에** 넣어야 합니다.

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("mods/", include("mods.urls")),   # ← 이 줄을 위에 추가
    path("", include("guide.urls")),
]
```

## 4단계. 메뉴 링크 — `guide/templates/guide/base.html`

`<nav>` 안에 한 줄 추가합니다.

```html
<a href="{% url 'ammo' %}">탄약</a>
<a href="{% url 'mods:index' %}">총기 모딩</a>   <!-- ← 이 줄 추가 -->
```

## 5단계. 테이블 생성

```powershell
.venv\Scripts\python.exe manage.py makemigrations mods
.venv\Scripts\python.exe manage.py migrate
```

## 6단계. 데이터 동기화

```powershell
.venv\Scripts\python.exe manage.py sync_mods
```

수 MB를 내려받고 슬롯 연결까지 계산하므로 **1~2분** 걸릴 수 있습니다.

---

## 명령어 옵션

| 옵션 | 설명 |
|---|---|
| `--lang en` | 영어 이름으로 |
| `--mode pve` | PVE 가격 기준 (`regular` / `pve` / `pvp-season`) |
| `--no-slots` | 슬롯 연결 생략 → 훨씬 빠름. 1·3단계만 볼 때 |
| `--file items.json` | 네트워크 대신 저장해둔 파일에서 읽기 |

---

## 실행 결과 읽는 법 ⭐

동기화가 끝나면 이런 요약이 나옵니다.

```
분류 결과 → 총기 132 / 프리셋 210 / 부품 1450
  프리셋 210개 저장 (총기 연결 210개)
  슬롯 옵션 41230개 저장
```

**여기서 확인할 것 두 가지:**

### ① "총기 연결 0개" 경고가 뜬다면

프리셋의 `baseItem` 필드명이 다른 겁니다. 1단계 페이지는 뜨지만 총기별 그룹이 안 묶입니다.
`sync_mods.py`의 `save_presets()` 안에 있는 이 줄을 고치면 됩니다.

```python
base = pick(p, "baseItem", "base")   # ← 여기에 실제 필드명 추가
```

### ② "슬롯 연결이 0건" 경고가 뜬다면

정적 JSON에 슬롯 정보가 없거나 구조가 다른 겁니다. 2단계 페이지가 비게 됩니다.
`save_slot_options()`의 이 부분을 확인하세요.

```python
slots = pick(g.get("properties") or {}, "slots", default=[])
allowed = pick(filters, "allowedItems", "allowedItemIds", default=[])
```

두 경우 모두 **1단계(프리셋)와 3단계(부품 랭킹)는 정상 작동합니다.**
2단계만 안 되는 거라 앱 전체가 망가지지는 않습니다.

---

## 만들어진 페이지

| 주소 | 내용 |
|---|---|
| `/mods/` | 모딩 홈 — 수치 읽는 법, 우선순위 안내 |
| `/mods/presets/` | 1단계 · 완성 프리셋을 기반 총기별로 묶어 비교 |
| `/mods/weapons/` | 2단계 · 총기 목록 |
| `/mods/weapons/<id>/` | 2단계 · 슬롯 트리 (슬롯당 상위 8개) |
| `/mods/parts/` | 3단계 · 부품 가성비 랭킹 (예산·종류 필터) |

---

## 성능 주의사항

**슬롯 옵션은 행 수가 수만 개가 될 수 있습니다.** (총기 × 슬롯 × 장착가능부품)
SQLite로도 충분히 감당되지만, 화면에서는 반드시 잘라서 보여줘야 합니다.

- 총기 상세: 슬롯당 상위 **8개**만 표시
- 부품 랭킹: 상위 **120개**만 표시

이 숫자를 늘리시려면 `mods/views.py`의 `mod_list[:8]`, `items[:120]`을 고치면 되는데,
너무 키우면 브라우저가 버벅입니다. 대신 **페이지네이션**을 붙이는 게 정석이에요.

---

## 데이터 구조 메모 (재귀 문제)

타르코프 모딩은 **재귀 구조**입니다.

```
총 → 슬롯 → 부품 → 그 부품의 슬롯 → 또 부품 → ...
```

이 앱은 의도적으로 **깊이 1단계까지만** 저장합니다.
전체 트리를 펼치면 조합이 기하급수로 늘어나 DB와 화면이 모두 감당하지 못합니다.

부품에 하위 슬롯이 있으면 화면에 `+슬롯` 태그가 붙습니다.
"이 부품에 또 뭔가 끼울 수 있다"는 신호이고, 그 다음 단계는 위키 링크로 넘깁니다.

나중에 전체 빌더로 확장하고 싶으시면, DB에 트리를 저장하는 대신
**사용자가 부품을 고를 때마다 그 시점에만 하위 슬롯을 조회**하는 방식(lazy loading)으로 가야 합니다.
