# 타르코프 초보 정리표 (Django)

Escape from Tarkov의 **의료품 · 가방/리그 · 탄약**을 초보자 관점에서 정리해 보여주는 Django 웹앱입니다.
데이터와 아이템 이미지는 커뮤니티 오픈 API인 [tarkov.dev](https://tarkov.dev/api/)에서 가져옵니다. (API 키 불필요)
정확히는 GraphQL이 아니라 정적 JSON 배포본인 `json.tarkov.dev`를 씁니다. GraphQL 쪽이 종종 죽어 있어서입니다.

---

## 실행 방법 (Step by Step)

### 1단계. 내려받고 폴더로 이동

```bash
git clone https://github.com/sinaint/tarkov_guide.git
cd tarkov_guide
```

> 💡 OneDrive로 동기화되는 폴더나 한글이 들어간 경로는 피해 주세요. 가끔 인코딩 문제가 생깁니다.

### 2단계. 가상환경 만들기 (권장)

```bash
python -m venv .venv
.venv\Scripts\activate
```

앞에 `(.venv)`가 붙으면 성공입니다.

### 3단계. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 4단계. 데이터베이스 만들기

```bash
python manage.py migrate
```

### 5단계. 실제 데이터 내려받기 ⭐

```bash
python manage.py sync_tarkov
```

약 18MB를 받아오며 10초 안팎 걸립니다.
`완료! 신규 381개 / 갱신 0개 / 삭제 0개` 처럼 나오면 성공입니다.

> 두 번째부터는 훨씬 빠릅니다. 아래 **자동 갱신** 항목을 참고하세요.

### 6단계. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 http://127.0.0.1:8000 접속!

---

## 자주 쓰는 명령어

| 명령어 | 설명 |
|---|---|
| `python manage.py sync_tarkov` | 전체 갱신 (한국어 이름) |
| `python manage.py sync_tarkov --lang en` | 영어 이름으로 받기 |
| `python manage.py sync_tarkov --only ammo` | 탄약만 갱신 |
| `python manage.py sync_tarkov --mode pve` | PVE 모드 가격 기준 |
| `python manage.py sync_tarkov --force` | 변경이 없어도 강제로 다시 저장 |
| `python manage.py test guide` | 동기화 판단 로직 자체 점검 (인터넷 불필요) |
| `python manage.py createsuperuser` | 관리자 계정 생성 (`/admin/`에서 데이터 확인용) |

`seed_demo.py`는 인터넷 없이 화면만 확인해 보고 싶을 때 쓰는 가짜 데이터 스크립트입니다.
실제 데이터를 받은 뒤에는 실행하지 마세요. (기존 데이터를 지웁니다)
실수로 돌렸더라도 `sync_tarkov`를 한 번 더 실행하면 가짜 데이터는 자동으로 지워집니다.

`probe_json_api.py`는 API 응답 구조가 또 바뀌었을 때 실제 모양을 들여다보는 조사용 스크립트입니다.

---

## 자동 갱신 ⏰

원본 데이터는 하루 한두 번 갱신됩니다. **매번 18MB를 다시 받지는 않습니다.**

`sync_tarkov`는 서버가 준 ETag를 `.sync_etag.json`에 적어두고, 다음 실행 때
"그때 그대로냐?"고 먼저 물어봅니다. 그대로면 서버가 `304`(내용 없음)만 돌려주므로
**2초 만에 아무것도 안 받고 끝납니다.**

```
요청 중... https://json.tarkov.dev/regular/items
  → 변경 없음 (304)
원본이 그대로입니다. 갱신할 내용이 없습니다.
```

그래서 자주 돌려도 부담이 없고, 갱신되는 순간 바로 따라잡습니다.
1시간마다 자동 실행하려면 (관리자 권한 PowerShell):

```powershell
schtasks /Create /TN "tarkov_guide sync" /SC HOURLY /F /TR ^
  "'C:\Users\<사용자>\...\tarkov_guide\.venv\Scripts\python.exe' 'C:\Users\<사용자>\...\tarkov_guide\manage.py' sync_tarkov"
```

경로만 본인 것으로 바꾸면 됩니다. 폴더 위치와 상관없이 동작합니다.
확인은 `schtasks /Query /TN "tarkov_guide sync"`, 해제는 `/Delete /TN "tarkov_guide sync" /F`.

---

## 폴더 구조

```
tarkov_guide/
├─ manage.py                 ← 모든 명령어의 진입점
├─ config/
│  ├─ settings.py            ← 설정 (DB, 앱 목록, 언어 등)
│  └─ urls.py                ← 주소 → 앱 연결
└─ guide/
   ├─ models.py              ← 데이터 구조 정의
   ├─ views.py               ← 페이지별 로직
   ├─ urls.py                ← 페이지 주소
   ├─ admin.py               ← 관리자 화면 설정
   ├─ management/commands/
   │  └─ sync_tarkov.py      ← ⭐ API에서 데이터 받아오는 코드
   └─ templates/guide/       ← 화면(HTML)
      ├─ base.html           ← 공통 레이아웃 + CSS
      ├─ index.html
      ├─ meds.html
      ├─ storage.html
      └─ ammo.html
```

---

## 자주 만나는 오류

| 증상 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | 가상환경 활성화를 잊었거나 3단계를 안 했습니다 |
| `ModuleNotFoundError: No module named 'config'` | `manage.py`가 있는 폴더에서 실행해야 합니다 |
| `응답 형식 오류` / `data.items 를 찾지 못했습니다` | 패치로 응답 구조가 바뀐 경우입니다. `python probe_json_api.py`로 실제 모양을 확인한 뒤 `sync_tarkov.py`를 고치세요 |
| 이름이 `5447a9cd... Name` 으로 나옴 | 번역표(`items_ko`)를 못 받은 경우입니다. `--force`로 다시 받아보세요 |
| 이미지가 안 보임 | 인터넷 연결 또는 광고 차단 확장 프로그램이 tarkov.dev 이미지를 막고 있는지 확인 |
| 아이템이 0개 | 5단계 `sync_tarkov`를 먼저 실행해야 합니다 |

---

## 다음에 확장하면 좋을 것

1. **총기 모딩 프리셋** — API의 `preset` 타입에 완성된 총 조합이 들어 있습니다 (`ergonomics`, `recoilVertical` 등)
2. **방탄복 페이지** — `armor` 타입 + `ItemPropertiesArmor` (클래스, 내구도, 방어 부위)
3. **탄 vs 방탄 관통 계산기** — 관통력과 방탄 클래스를 넣으면 뚫리는지 알려주는 기능
4. **방어 부위 한글화** — 리그의 `zones` 값도 번역표에 들어 있습니다 (`Collider Type Eyes` → `머리, 눈`)
5. **가격 자동 갱신** — 위 **자동 갱신** 항목대로 작업 스케줄러에 등록

---

## 주의사항

- 아이템 이미지와 게임 데이터의 저작권은 **Battlestate Games**에 있습니다. 개인 학습·비상업 용도로만 사용하세요.
- 수치는 **와이프와 패치마다 바뀝니다.** `sync_tarkov`를 주기적으로 실행하세요.
- API를 짧은 간격으로 반복 호출하지 마세요. 하루 1~2회면 충분합니다.
- `settings.py`의 `SECRET_KEY`와 `DEBUG = True`는 개발 전용입니다. 외부에 공개할 때는 반드시 바꿔주세요.
