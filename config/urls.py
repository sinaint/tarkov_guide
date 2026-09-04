from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # ⚠️ guide.urls 가 빈 경로("")를 잡으므로 반드시 그 위에 둡니다
    path("mods/", include("mods.urls")),
    path("", include("guide.urls")),  # 메인 페이지를 guide 앱에 위임
]
