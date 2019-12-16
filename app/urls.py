from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('index/',views.index,name='index'),
    path('',views.login,name='login'),
    path('register/',views.register,name='register'),
    path('registers/',views.registers,name='registers'),
    path('exit/',views.exit,name='exit'),
    path('user_information/', views.user_information, name='user_information'),
    path('updata_infor/',views.upadta_infor,name='upadta_infor'),
    path('pc-geetest/register', views.pcgetcaptcha,name='pcgetcaptcha'),
    path('pc-geetest/validate',views.pcvalidate,name='pcvalidate'),
    path('tasks/',views.tasks,name='tasks'),
    path('d_tasks/<id>',views.d_tasks,name='d_tasks'),
    path('tasks_list/<pk>',views.tasks_list,name='tasks_list'),
    path('task_list/<id>',views.task_list,name='task_list'),
    path('issue/',views.issue,name='issue'),
    url(r"^active/(?P<token>.*)$",views.active.as_view(), name="active"),
    url(r'^editor/',views.editor,name='editor'),
    path('image_save/',views.image_save,name="image_save"),
    path('list/',views.list,name='list'),
    path('lists/<pk>',views.lists,name='lists')
]+static(settings.MEDIA_URL,documment_root = settings.MEDIA_ROOT)

