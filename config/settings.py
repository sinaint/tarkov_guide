"""
Django 설정 파일
초보자용으로 꼭 필요한 항목만 남기고 주석을 달아두었습니다.
"""
import os
from pathlib import Path

# 프로젝트 최상위 폴더 (manage.py 가 있는 위치)
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env(path):
    """
    .env 파일을 읽어 환경변수로 올립니다.

    이미 설정된 환경변수가 이깁니다(setdefault). 배포 환경에서 주입한 진짜 값을
    실수로 남아있던 .env 파일이 덮어쓰면 안 되기 때문입니다.
    파일이 없으면 조용히 넘어갑니다 — 배포 환경에는 보통 .env 가 없습니다.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        # 값 뒤에 붙은 인라인 주석을 잘라냅니다.
        #   DJANGO_DEBUG=1  # 개발용   →   "1"
        # 이걸 안 하면 값이 "1  # 개발용" 이 되어 비교가 조용히 실패합니다.
        # 값 자체에 #이 들어갈 수 있으므로, 앞에 공백이 붙은 # 만 주석으로 봅니다.
        if " #" in value:
            value = value.split(" #", 1)[0].strip()
        os.environ.setdefault(key.strip(), value.strip("\"'"))


load_env(BASE_DIR / ".env")

# ── 시크릿은 코드에 두지 않습니다 ──────────────────────────────
# 배포할 때는 DJANGO_SECRET_KEY 를 반드시 주입하세요.
# 아래 기본값은 로컬에서 최소한 실행은 되게 하려는 값이며, 운영용이 아닙니다.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-for-production")

# 기본값을 False 로 둡니다. 환경변수를 깜빡하고 배포해도
# 에러 페이지에 설정값·소스코드가 노출되지 않습니다.
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# testserver 는 Django 자동 테스트용 주소입니다.
# 쉼표로 나눈 뒤 앞뒤 공백을 제거합니다.
#   "a.com, b.com" 처럼 공백을 넣어도 " b.com" 이 되지 않도록.
# (공백이 남으면 그 주소로 들어온 요청이 전부 500 에러가 납니다)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
    ).split(",")
    if h.strip()  # 맨 끝 쉼표 등으로 생긴 빈 값 제거
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # 숫자에 천 단위 콤마를 넣어줍니다
    "guide",  # 우리가 만든 앱
    "mods",   # 총기 모딩 앱
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # 응답에 X-Frame-Options 헤더를 붙여 클릭재킹을 막습니다.
    # (남의 사이트가 이 페이지를 투명한 iframe 으로 덮어씌워 클릭을 가로채는 공격)
    # Django 가 startproject 시 기본으로 넣어주는 미들웨어인데 빠져 있었습니다.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        # 각 앱의 templates/ 폴더를 자동으로 찾아줍니다
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite: 별도 설치 없이 파일 하나로 동작하는 가벼운 DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# 관리자(/admin/) 계정 비밀번호 규칙입니다.
# 비워두면 "1234" 같은 비밀번호도 통과하는데, admin 주소는
# 인터넷에 올리는 순간 자동 스캔 봇이 가장 먼저 두드리는 문입니다.
AUTH_PASSWORD_VALIDATORS = [
    # 아이디·이메일과 비슷한 비밀번호 차단 (예: zero / zero1234)
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # 최소 길이
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    # 흔히 쓰이는 비밀번호 2만 개 목록과 대조
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # 숫자로만 이루어진 비밀번호 차단
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 한국어 / 한국 시간대 설정
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ── 배포 환경 보안 설정 ────────────────────────────────────────
# DEBUG 가 False 일 때(= 실제 배포)만 켭니다.
# 로컬 개발은 http 라서 아래를 항상 켜면 사이트에 접속 자체가 안 됩니다.
#
# 적용 후 점검:
#   $env:DJANGO_DEBUG="0"
#   .venv\Scripts\python.exe manage.py check --deploy
if not DEBUG:
    # http 로 들어온 요청을 https 로 돌려보냅니다
    SECURE_SSL_REDIRECT = True

    # 세션·CSRF 쿠키를 https 에서만 전송합니다.
    # (평문 http 로 새어나가면 로그인 세션을 통째로 탈취당할 수 있습니다)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # 자바스크립트가 세션 쿠키를 읽지 못하게 합니다 (XSS 피해 축소)
    SESSION_COOKIE_HTTPONLY = True

    # 외부 사이트에서 넘어온 요청에는 쿠키를 보내지 않습니다 (CSRF 방어 보강)
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

    # HSTS: 브라우저에게 "이 사이트는 앞으로 https 로만 접속하라" 고 기억시킵니다.
    #
    # ⚠️ 주의: 한 번 기억되면 이 기간 동안 되돌리기 어렵습니다.
    #    인증서가 만료되면 사이트가 통째로 안 열립니다.
    #    처음엔 1시간(3600)으로 두고, 인증서 자동 갱신이 도는 걸 확인한 뒤
    #    1년(31536000)으로 올리세요.
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # 리버스 프록시(Nginx, AWS ALB 등) 뒤에 있을 때,
    # 원래 요청이 https 였는지 판단하는 근거가 되는 헤더입니다.
    #
    # ⚠️ 주의: 신뢰할 수 있는 프록시 뒤에 있을 때만 켜세요.
    #    프록시 없이 켜면 공격자가 이 헤더를 위조해 https 인 척할 수 있습니다.
    #    프록시 없이 직접 배포한다면 아래 줄을 주석 처리하세요.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
