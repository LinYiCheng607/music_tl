from django.shortcuts import render, redirect
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from index.models import *
from django.db.models import Q

def searchview(request, page):
    if request.method == 'GET':
        # 热搜歌曲
        search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:6]
        kword = request.session.get('kword', '')
        if kword:
            song_info = Song.objects.values('song_id', 'song_name', 'song_singer', 'song_time').\
                filter(Q(song_name__contains=kword) | Q(song_singer=kword)).order_by('-song_release').all()
        else:
            song_info = Song.objects.values('song_id', 'song_name', 'song_singer', 'song_time').\
                order_by('-song_release').all()
        paginator = Paginator(song_info, 20)  # 每页20首
        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            contacts = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        # 分页逻辑，只显示10个分页
        total_pages = paginator.num_pages
        current_page = contacts.number
        if total_pages <= 10:
            page_range = range(1, total_pages + 1)
        else:
            if current_page <= 6:
                page_range = range(1, 11)
            elif current_page + 4 > total_pages:
                page_range = range(total_pages - 9, total_pages + 1)
            else:
                page_range = range(current_page - 5, current_page + 5)
        # 添加歌曲搜索次数
        song_exist = Song.objects.filter(song_name=kword)
        if song_exist:
            song_id = song_exist[0].song_id
            dynamic_info = Dynamic.objects.filter(song_id=int(song_id)).first()
            if dynamic_info:
                dynamic_info.dynamic_search += 1
                dynamic_info.save()
            else:
                dynamic = Dynamic(dynamic_plays=0, dynamic_search=1, dynamic_down=0, song_id=song_id)
                dynamic.save()
        return render(request, 'search.html', {
            'contacts': contacts,
            'search_song': search_song,
            'page_range': page_range,
            'current_page': current_page,
            'total_pages': total_pages,
        })
    else:
        # 处理POST请求，并重定向到搜索页面
        request.session['kword'] = request.POST.get('kword', '')
        return redirect('/search/1.html')