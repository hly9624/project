# -*- coding: utf-8 -*-

import pdb
import logging
from django.shortcuts import render, redirect, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from django.db import connection
from django.db.models import Count
from models import *
from myapp.forms import *

logger = logging.getLogger('myapp.views')
def global_setting(request):
     category_list = Category.objects.all()[:6]
     ad_list = Ad.objects.all()[:6]
     archive_list = Article.objects.distinct_date()
     article_list = Article.objects.all()
     #标签云数据
     tag_list = Tag.objects.all()
     #友情链接数据
     link_list = Links.objects.all()
     #文章排行榜数据
     #文章排行榜数据-按点击排序
     click_article_list = article_list.order_by('-click_count')[:6]
     #文章排行榜数据-按评论排序
     comment_article_list = []
     recommend_article_list = Article.objects.filter(is_recommend = True)
     result_list = Comment.objects.with_counts()
     #文章排行榜数据-只选推荐的
     for article_id in result_list:
             article = Article.objects.get(id=article_id)
             comment_article_list.append(article)
     return {'SITE_URL':settings.SITE_URL,
             'SITE_NAME':settings.SITE_NAME,
             'SITE_DESC':settings.SITE_DESC,
             'category_list':category_list,
             'archive_list':archive_list,
             'ad_list':ad_list,
             'tag_list':tag_list,
             'link_list':link_list,
             'article_list':article_list,
             'click_article_list':click_article_list,
             'comment_article_list':comment_article_list,
             'recommend_article_list':recommend_article_list,
            }

def index(request):
    try:
        # 最新文章数据
        article_list = Article.objects.all()
        article_list = getPage(request, article_list)
    except Exception as e:
        print e
        logger.error(e)
    return render(request, 'index.html', locals())

def archive(request):
    pass
    # try:
    #     # 先获取客户端提交的信息
    #     year = request.GET.get('year', None)
    #     month = request.GET.get('month', None)
    #     article_list = Article.objects.filter(date_publish__icontains=year+'-'+month)
    #     article_list = getPage(request, article_list)
    # except Exception as e:
    #     logger.error(e)
    return render(request, 'archive.html', locals())


def tag(request):
    try:
        tag = request.GET.get('tag',None)
        tag = Tag.objects.get(name = tag)
        article_list = tag.article_set.all()
        article_list = getPage(article_list)
    except Exception as e:
        logger.error(e)
    return render(request, 'tag.html', locals())

def getPage(request, article_list):
    paginator = Paginator(article_list, 3)
    try:
        page = int(request.GET.get('page', 1))
        article_list = paginator.page(page)
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        article_list = paginator.page(1)
    return article_list

def article(request):
    #pbd.set_trace()
    try:
        # 获取文章id
        id = request.GET.get('id', None)
        try:
            # 获取文章信息
            article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
            return render(request, 'failure.html', {'reason': '没有找到对应的文章'})

        # 评论表单
        comment_form = CommentForm({'author': request.user.username,
                                    'email': request.user.email,
                                    'url': request.user.url,
                                    'article': id} if request.user.is_authenticated() else{'article': id})
        # 获取评论信息
        comments = Comment.objects.filter(article=article).order_by('id')
        comment_list = []
        for comment in comments:
            for item in comment_list:
                if not hasattr(item, 'children_comment'):
                    setattr(item, 'children_comment', [])
                if comment.pid == item:
                    item.children_comment.append(comment)
                    break
            if comment.pid is None:
                comment_list.append(comment)
    except Exception as e:
        print e
        logger.error(e)
    return render(request, 'article.html', locals())

def comment_post(request):
    try:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            #获取表单信息
            comment = Comment.objects.create(username=comment_form.cleaned_data["author"],
                                             email=comment_form.cleaned_data["email"],
                                             url=comment_form.cleaned_data["url"],
                                             content=comment_form.cleaned_data["comment"],
                                             article_id=comment_form.cleaned_data["article"],
                                             user=request.user if request.user.is_authenticated() else None)
            comment.save()
        else:
            return render(request, 'failure.html', {'reason': comment_form.errors})
    except Exception as e:
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])

def do_logout(request):
    try:
        logout(request)
    except Exception as e:
        print (e)
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])
def do_reg(request):
    try:
        if request.method == 'POST':
            reg_form = RegForm(request.POST)
            if reg_form.is_valid():
                # 注册
                user = User.objects.create(username=reg_form.cleaned_data["username"],
                                    email=reg_form.cleaned_data["email"],
                                    url=reg_form.cleaned_data["url"],
                                    password=make_password(reg_form.cleaned_data["password"]),)
                user.save()

                # 登录
                user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                login(request, user)
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': reg_form.errors})
        else:
            reg_form = RegForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'reg.html', locals())

def do_login(request):
    try:
        if request.method == 'POST':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                # 登录
                username = login_form.cleaned_data["username"]
                password = login_form.cleaned_data["password"]
                user = authenticate(username=username, password=password)
                if user is not None:
                    user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                    login(request, user)
                else:
                    return render(request, 'failure.html', {'reason': '登录验证失败'})
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': login_form.errors})
        else:
            login_form = LoginForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'login.html', locals())

def category(request):
    try:
        # 先获取客户端提交的信息
        cid = request.GET.get('cid', None)
        try:
            category = Category.objects.get(pk=cid)
        except Category.DoesNotExist:
            return render(request, 'failure.html', {'reason': '分类不存在'})
        article_list = Article.objects.filter(category=category)
        article_list = getPage(request, article_list)
    except Exception as e:
        logger.error(e)
    return render(request, 'category.html', locals())
