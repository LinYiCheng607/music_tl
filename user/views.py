from django.shortcuts import render, redirect
from user.models import *
from django.db.models import Q
from django.contrib.auth import logout, login
from django.contrib.auth.hashers import check_password
from .form import MyUserCreationForm
from index.models import *
import json
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models import Sum
from django.http import JsonResponse
# Create your views here.


def loginview(request):
    # 表单对象
    user = MyUserCreationForm()
    # 表单提交
    if request.method == 'POST':
        # 判断表单提交时用户登录还是用户注册
        # 用户登录
        if request.POST.get('loginUser', ''):
            loginUser = request.POST.get('loginUser', '')
            password = request.POST.get('password', '')
            if MyUser.objects.filter(Q(mobile=loginUser) | Q(username=loginUser)):
                user = MyUser.objects.filter(Q(mobile=loginUser) | Q(username=loginUser)).first()
                if check_password(password, user.password):
                    login(request, user)
                    return redirect('/user/home/1.html')
                else:
                    tips = '密码错误'
            else:
                tips = '用户不存在'
        else:
            # 用户注册
            user = MyUserCreationForm(request.POST)
            # print(user)
            if user.is_valid():
                user.save()
                tips = '注册成功'
            else:
                if user.errors.get('username'):
                    tips = user.errors.get('username', '注册失败1')
                else:
                    tips = user.errors.get('mobile', '注册失败2')
    return render(request, 'login.html', locals())


def logoutview(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/user/login.html')
def homeview(request, page):
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:6]
    song_count_qs = (
        SongLog.objects
        .filter(user=request.user)
        .values('song', 'song__song_id', 'song__song_name', 'song__song_singer', 'song__song_time')
        .annotate(listen_count=Sum('listen_count'))
        .order_by('-listen_count', '-song')
    )
    song_info = [
        {
            'song_id': item['song__song_id'],
            'song_name': item['song__song_name'],
            'song_singer': item['song__song_singer'],
            'song_time': item['song__song_time'],
            'listen_count': item['listen_count'] or 0,
        }
        for item in song_count_qs
    ]
    # print(song_info)  # <---- 检查这里输出的内容
    paginator = Paginator(song_info, 10)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    return render(request, 'home.html', {
        'contacts': contacts,
        'search_song': search_song,
    })

@login_required
def song_analysis(request):
    # 统计最近7天每天听歌数量
    today = timezone.now().date()
    days = 7
    line_labels = []
    line_data = []
    for i in range(days):
        day = today - timedelta(days=days - i - 1)
        line_labels.append(day.strftime('%Y-%m-%d'))
        cnt = SongLog.objects.filter(user=request.user, listen_time__date=day).count()
        line_data.append(cnt)

    # 统计不同类型的听歌次数
    # 注意：Song模型的类型字段叫 song_type
    pie_qs = (
        SongLog.objects
        .filter(user=request.user)
        .values('song__song_type')
        .annotate(value=Count('id'))
        .order_by('-value')
    )
    pie_data = []
    for item in pie_qs:
        # item['song__song_type'] 可能为None，需要兜底
        pie_data.append({
            'name': item['song__song_type'] or '未知',
            'value': item['value']
        })

    context = {
        'line_labels': json.dumps(line_labels, ensure_ascii=False),
        'line_data': json.dumps(line_data, ensure_ascii=False),
        'pie_data': json.dumps(pie_data, ensure_ascii=False),
        # 你可以补充热门搜索/推荐等
        'search_song': [],
    }
    return render(request, 'song_analysis.html', context)

@login_required
def update_user_info(request):
    if request.method == "POST":
        user = request.user
        user.nickname = request.POST.get("nickname", user.nickname)
        user.email = request.POST.get("email", user.email)
        user.qq = request.POST.get("qq", user.qq)
        user.mobile = request.POST.get("mobile", user.mobile)
        user.bio = request.POST.get("bio", user.bio)
        user.save()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "nickname": user.nickname,
                "email": user.email,
                "qq": user.qq,
                "mobile": user.mobile,
                "bio": user.bio,
            })
        return redirect("home", 1)
    return redirect("home", 1)