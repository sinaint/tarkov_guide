from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("guide.urls")),  # 메인 페이지를 guide 앱에 위임
]
