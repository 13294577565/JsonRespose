from django.shortcuts import render,HttpResponse,redirect,reverse
import sqlite3
from django.http import JsonResponse
from django.views import View
from .models import *
from django.http import HttpResponse
from geetest import GeetestLib
from celery_tasks.tasks import send_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from itsdangerous import SignatureExpired
import datetime
from django.forms.models import model_to_dict
import json
from django.utils import timezone
import pandas as pd
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage,InvalidPage



pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"
mobile_geetest_id = "7c25da6fe21944cfe507d2f9876775a9"
mobile_geetest_key = "f5883f4ee3bd4fa8caec67941de1b903"

def pcgetcaptcha(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)
def pcvalidate(request):
    if request.method == "POST":
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        result = "<html><body><h1>登录成功</h1></body></html>" if result else "<html><body><h1>登录失败</h1></body></html>"
        return HttpResponse(result)
    return HttpResponse("error")

def index(request):
    return render(request,'index.html')

def login(request):
    if request.method=="POST":
        a = request.POST.get('username')
        b = request.POST.get('password')
        if a and b:
            c = UserLogin.objects.filter(user_name=a,password=b)
            if c:
                request.session["username"] = a
                return redirect(reverse('index'))
            elif UserLogin.objects.filter(is_active=0):
                return render(request, 'register.html', {'error': "请先激活您的账号"})
            else:
                return render(request,'login.html')
        else:
            return render(request,'login.html')
    else:
        d = request.session.get('username')
        if d:
            return redirect('index')
        else:
            return render(request, 'login.html')

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        sex = request.POST.get('sex')
        adress = request.POST.get('adress')
        education = request.POST.get('education')
        email = request.POST.get('email')
        print(username,password,phone,age,sex,adress,education)
        if username and password and phone and age and sex and adress and education:
            if UserLogin.objects.filter(user_name=username):
                return render(request,'register.html',{'error':"账户已存在请重新输入"})
            elif UserLogin.objects.filter(phone=phone):
                return render(request, 'register.html', {'error': "该电话号已被绑定！！"})
            else:
                user = UserLogin.objects.create(user_name=username,password=password,phone=phone,age=age,sex=sex,adress=adress,education=education,teacher_id=0,email=email,is_active=0)
                UserLogin.is_active = 0
                # 加密发邮箱，一个小时激活码过期
                serializer = Serializer(settings.SECRET_KEY, 3600)
                #             #传入id
                info = {'confirm': user.id}
                # 把用户id进行加密，decode()进行编码
                token = serializer.dumps(info).decode()
                send_active_email.delay(username=username,email=email, token=token)
                print(email,username,token)
                return redirect(reverse('login'))
        else:
            return render(request, 'index.html')
    else:
        return render(request,'register.html')



def registers(request):
    result = {"code": 10000, "content": ""}
    data = request.GET
    username = data.get("code")
    print(username)
    if username == '':
        print('2')
        result['code'] = 10001
        print('1')
        result['content'] = ""
    else:
        user = UserLogin.objects.filter(user_name=username)
        if user:
            result['code'] = 10000
            result['content'] = "false"
        else:
            result['code'] = 10002
            result['content'] = "true"
    return JsonResponse(result)


#激活
class active(View):
    def get(self, request,token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            user = UserLogin.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('login'))
        except SignatureExpired as e:
            return HttpResponse('您的激活码已经过期')



def exit(request):
    request.session.flush()
    return render(request,'register.html')


def user_information(request):
    username = request.session.get('username')
    content = UserLogin.objects.filter(user_name=username)
    return render(request,'user_information.html',{"content":content})






def upadta_infor(request):
    if request.method=='POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        sex = request.POST.get('sex')
        adress = request.POST.get('adress')
        education = request.POST.get('education')
        email = request.POST.get('email')
        brief = request.POST.get('brief')
        trait = request.POST.get('trait')
        if username and password:
            user = request.session.get('username')
            UserLogin.objects.filter(user_name=username).update(user_name=username,name=name,password=password,phone=phone,age=age,sex=sex,adress=adress,education=education,email=email,brief=brief,trait=trait,)
            return redirect(reverse(index))
    else:
        username = request.session.get('username')
        content = UserLogin.objects.filter(user_name=username)
        return render(request,'updata_informations.html',{"content":content})

def tasks(request):

    username = request.session['username']
    error = UserLogin.objects.get(user_name=username)
    content = Task.objects.all()
    paginator = Paginator(content,2)

    if request.method == 'GET':
        page = request.GET.get('page')
        try:
            content = paginator.page(page)
        except PageNotAnInteger:
            content = paginator.page(1)
        except InvalidPage:
            return HttpResponse("找不到页面")
        except EmptyPage:
            content = paginator.page(paginator.num_pages)
        return render(request,'tasks.html',{"content":content,"error":error.teacher_id})

def d_tasks(request,id):
    try:
        user = Task.objects.filter(id=id)
        user.delete()
        return redirect(reverse('tasks'))
    except:
        return redirect(reverse('tasks'))

li = []
def task_list(request,id):
    li.append(id)
    print(li)
    user = Task.objects.filter(id=id)
    data = UserLogin.objects.all()
    return render(request,'task_list.html',{"user":user,"data":data})



def tasks_list(request,pk):
    list = ''.join(li[:1])
    print(list)
    if request.method =="POST":
        data = UserLogin.objects.all()
        datas = request.POST.get('data')
        for i in data:
            if datas == '1':
                if Middle.objects.filter(mi_user_id=pk,wancheng=1,mi_task_id=list):
                    middle = Middle.objects.filter(mi_user_id=pk,wancheng=1)
                    middles = middle = Middle.objects.filter(mi_user_id=pk,wancheng=0 and 1)
                    middles = middle.count()
                    return render(request,'task_list.html',{"error":middle})
                else:
                    Middle.objects.create(mi_user_id=pk,mi_task_id=list,wancheng=1)
                    li.clear()
                    return redirect(reverse('user_information'))
            else:
                Middle.objects.create(mi_user_id=pk, mi_task_id=list, wancheng=0)
    else:
        if Middle.objects.filter(mi_user_id=pk,wancheng=1):
            return render(request,'task_list.html',{"error":"该学生已完成任务"})



def issue(request):
    user = request.session.get('username')
    contents = request.POST.get('comment_content')
    print(contents)
    content = UserLogin.objects.filter(user_name=user)
    if content.filter(teacher_id=0):
        return redirect(reverse('index'))
    elif contents:
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        Task.objects.create(task_content=contents, task_show_time=time)
        return render(request,'index.html')
    else:
        return render(request,'issue.html')




def image_save(request):
    if request.method == "POST":
        myfile = request.FILES.get('myfile')
        print(myfile)
        user = request.session.get('username')
        auser = UserLogin.objects.get(user_name=user)
        auser.img = myfile
        auser.save()
        return redirect(reverse('index'))
    else:
        return render(request,'user_information.html')



def list(request):
    data = UserLogin.objects.all()
    paginator = Paginator(data, 1)
    # page = Paginator(data,2)
    if request.method == 'GET':
        page = request.GET.get('page')
        try:
            members = paginator.page(page)
        except PageNotAnInteger:
            members = paginator.page(1)
        except InvalidPage:
            return HttpResponse("找不到页面")
        except EmptyPage:
            members = paginator.page(paginator.num_pages)
        return render(request,'list.html',  {"data":members})



def lists(request,pk):
    content = UserLogin.objects.filter(id=pk)
    return render(request,'lists.html',{"content":content})





#测试富文本编辑器是否正确
def editor(request):
    return render(request,'editor.html')