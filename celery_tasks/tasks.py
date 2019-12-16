from celery import Celery
from JsonRespose import settings
from django.core.mail import send_mail
import os
import django
import time



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JsonRespose.settings")
django.setup()

app = Celery("celery_tasks.tasks", broker="redis://127.0.0.1:6379/4")

@app.task
def send_active_email(email,username,token):
    """发送用户激活邮件"""
    subject = "学生日常管理系统欢迎你" # 邮件标题
    message = '' # 邮件正文
    sender = settings.EMAIL_FROM # 发件人
    receiver = [email] # 收件人
    html_message = """<h1>%s 恭喜您注册学生日常管理系统</h1><br/><h3>请您在1小时内点击以下
    链接进行账户激活</h3><a href="http://127.0.0.1:8001/active/%s">http://127.0.0.1:8001/active/%s</a> """% (username,token,token)
    send_mail(subject,message,sender,receiver,html_message=html_message)
    # 为了体现出celery异步完成发送邮件，这里睡眠5秒
    # time.sleep(5)
