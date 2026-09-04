"""
Django 설정 파일
초보자용으로 꼭 필요한 항목만 남기고 주석을 달아두었습니다.
"""
from pathlib import Path

# 프로젝트 최상위 폴더 (manage.py 가 있는 위치)
BASE_DIR = Path(__file__).resolve().parent.parent

# 개발용 임시 키입니다. 실제 배포 시에는 환경변수로 빼주세요!
SECRET_KEY = "django-insecure-tarkov-guide-dev-only-change-me"

# 개발 중에는 True, 배포 시 반드시 False
DEBUG = True

# testserver 는 Django 자동 테스트용 주소입니다
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # 숫자에 천 단위 콤마를 넣어줍니다
    "guide",  # 우리가 만든 앱
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
