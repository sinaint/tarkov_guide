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
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env(BASE_DIR / ".env")

# ── 시크릿은 코드에 두지 않습니다 ──────────────────────────────
# 배포할 때는 DJANGO_SECRET_KEY 를 반드시 주입하세요.
# 아래 기본값은 로컬에서 최소한 실행은 되게 하려는 값이며, 운영용이 아닙니다.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-for-production")

# 기본값을 False 로 둡니다. 환경변수를 깜빡하고 배포해도
# 에러 페이지에 설정값·소스코드가 노출되지 않습니다.
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# testserver 는 Django 자동 테스트용 주소입니다
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
).split(",")

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

AUTH_PASSWORD_VALIDATORS = []

# 한국어 / 한국 시간대 설정
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
