from django.shortcuts import render, redirect, get_list_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView)
from .forms import LoginForm, UserCreateForm, CreateProfile, CreateReview, CreateComment, CreateReply
from .models import User, ProfileModel, ReviewModel, Counter, AnimeModel, AccessReview, Comment, ReplyComment, Like
import requests
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from django.http import HttpResponse
import io
import math
from django.db.models import Q
from django.db.models import Avg
# Create your views here.

class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'login.html'

class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'homepage.html'
    # model = ProfileModel

class UserCreate(generic.CreateView):
    form_class = UserCreateForm
    success_url = reverse_lazy('create_profile')
    template_name = 'signup.html'

    def form_valid(self,form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username = username, password = password)
        login(self.request,user)
        return response

class UserDelete(LoginRequiredMixin, generic.View):
    def get(self, *args, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        user.is_active = False
        user.save()
        logout(self.request)
        return render(self.request,'user_delete.html')

def homepage(request):
    return render(request,'homepage.html')

def create_profile(request):
    if request.method == 'POST':
        form = CreateProfile(request.POST, request.FILES)
        Counter.objects.create(username = request.user,genre_counter = '0/0/0/0/0/0/0/0')
        if form.is_valid():
            nickname = form.cleaned_data['nickname']
            gender = form.cleaned_data['gender']
            favarite_anime = form.cleaned_data['favarite_anime']
            avator = form.cleaned_data['avator']

            profile_model = ProfileModel(
                username = request.user,
                nickname = nickname,
                gender = gender,
                favarite_anime = favarite_anime,
                avator = avator
            )

            profile_models.save()

            return redirect('home')

    else:
        form = CreateProfile
    return render(request,'create_profile.html',{'form' : form})

def home(request):
    query_word = request.GET.get('q')
    if query_word:
        review_list = ReviewModel.objects.filter(
            Q(review_title__icontains=query_word) | 
            Q(anime__title__icontains=query_word) |
            Q(review_content__icontains=query_word)
        ).order_by('-post_date')
    else:
        review_list = ReviewModel.objects.all().order_by('-post_date')

    profile = ProfileModel.objects.get(user = request.user)

    comment_list = {}
    for review in ReviewModel.objects.all():
        comments = Comment.objects.filter(review = review)
        if comments.exists():
            comment_list[review] = comments.count()



    if AnimeModel.objects.exists():
        all_anime_list = AnimeModel.objects.all().order_by('title')

    # おすすめアニメの表示

    # 数字とジャンルを紐付け
    genre = {
    1:'SF',
    2:'ファンタジー',
    3:'コメディ',
    4:'バトル',
    5:'恋愛',
    6:'スポーツ',
    7:'青春',
    8:'戦争',
}

    counter = Counter.objects.get(user = request.user)  
    genre_counter = counter.counter
    top_genre = genre[genre_counter.index(max(genre_counter)) + 1]  # 最もアクセス数の高いジャンルを取得

    # アクセスしたアニメのうち、ジャンルがgenre_topと同じアニメ飲み抽出
    access_animes = []
    for ac_review in AccessReview.objects.filter(user = request.user):
        anime = ac_review.review.anime
        if anime in access_animes:
            pass
        else:
            if anime.genre == top_genre:
                access_animes.append(anime)
    
    # access_animesの評価平均を取得
    ac_evaluation_sum = [0,0,0,0,0]
    for anime in access_animes:
        reviews = ReviewModel.objects.filter(anime = anime)
        evaluation_sum = [0,0,0,0,0]

        for review in reviews:
            evaluation_sum = np.array(evaluation_sum) + np.array(review.evaluation)

        evaluation_ave = [n/reviews.count() for n in evaluation_sum]

        ac_evaluation_sum = np.array(ac_evaluation_sum) + np.array(evaluation_ave)
    
    ac_evaluation_ave = [n/len(access_animes) for n in ac_evaluation_sum]

    # 該当ジャンルの全てのアニメの類似度を取得
    anime_list = {}
    for anime in AnimeModel.objects.filter(genre = top_genre):
        if not anime in access_animes:
            reviews = ReviewModel.objects.filter(anime = anime)
            evaluation_sum = [0,0,0,0,0]
            if reviews.exists():
                
                for review in reviews:
                    evaluation_sum = np.array(evaluation_sum) + np.array(review.evaluation)
                
                evaluation_ave = [n/reviews.count() for n in evaluation_sum]

                evaluation_sub = np.array(ac_evaluation_ave) - np.array(evaluation_ave)
                evaluation_sqr = map(lambda x : x**2, evaluation_sub)
                similarity_value = math.sqrt(sum(evaluation_sqr))

                anime_list[anime] = similarity_value

                rec_anime = min(anime_list, key = anime_list.get)  # 類似度が最大のアニメを取得
                rec_anime_reviews = ReviewModel.objects.filter(anime = rec_anime).order_by('?')[:3]
                review_count = rec_anime_reviews.count()  # rec_animeのレビュー数を
                
                rank = anime_rank(rec_anime)

                return render(request,'home.html',{
                        'review_list' : review_list, 
                        'profile' : profile, 
                        'rec_anime' : rec_anime, 
                        'rank' : rank,
                        'review_count' : review_count,
                        'ac_evaluation_ave' : ac_evaluation_ave,
                        'rec_anime_reviews' : rec_anime_reviews,
                        'all_anime_list' : all_anime_list,
                        'comment_list' : comment_list})
        
    return render(request,'home.html',{'review_list' : review_list, 'profile' : profile, 'anime_list' : anime_list})

def profile(request,pk):
    profile = ProfileModel.objects.get(pk = pk)

    query_word = request.GET.get('q')
    if query_word:
        review_list = ReviewModel.objects.filter(user = profile.user).filter(
            Q(review_title__icontains=query_word) | 
            Q(anime__title__icontains=query_word) |
            Q(review_content__icontains=query_word)
        ).order_by('-post_date')
    else:
        review_list = ReviewModel.objects.filter(user = profile.user).order_by('-post_date')

    review_num = ReviewModel.objects.filter(user = profile.user).count()
    if review_list.exists():
        return render(request, 'profile.html', {'profile' : profile, 'review_list' : review_list,'review_num' : review_num})
    else:
        review_num = 0
        context = '投稿レビューはありません'
        return render(request, 'profile.html',{'profile' : profile, 'context' : context, 'review_num' : review_num})

def create_review(request):
    profile = ProfileModel.objects.get(user = request.user)  # profileを取得

    if request.method == 'POST':
        # AnimeModelに投稿したアニメデータを保存
        anime = request.POST.get('anime')  # 投稿したアニメ名を取得

        if not AnimeModel.objects.filter(title = anime).exists():  # アニメ一覧に該当アニメがない場合
            context = {'context' : '未登録もしくは入力したタイトルに間違いがあります。'}
            return render (request, 'create_review.html', context)
        
        elif ReviewModel.objects.filter(user = request.user).filter(anime__title = anime).exists():  # すでにレビュー済みのアニメの場合
            context = {'context' : 'すでにレビュー済みのアニメです'}
            return render(request, 'create_review.html', context)
        
        else:
            form = CreateReview(request.POST or None)

            if form.is_valid():
                # Pythonの型に変換
                anime = form.cleaned_data['anime']
                review = form.cleaned_data['review']
                evaluation = [
                    form.cleaned_data['eva_senario'],
                    form.cleaned_data['eva_drawing'],
                    form.cleaned_data['eva_music'],
                    form.cleaned_data['eva_character'],
                    form.cleaned_data['eva_cv']
                ]

                # reviewのタイトルを取得
                split_review = review.splitlines()
                review_title = split_review.pop(0)
                # review_contentの取得
                if request.POST.get('spoiler') == '1':
                    split_review.insert(0,'※ネタバレを含む')
                review_content = '\r\n'.join(split_review)

                # evaluation_aveの取得
                evaluation_ave = sum(evaluation) / len(evaluation)

                # Reviewを作成
                ReviewModel.objects.create(
                    user = request.user,
                    profile = ProfileModel.objects.get(user = request.user),
                    anime = AnimeModel.objects.get(title = anime),
                    review_title = review_title,
                    review_content = review_content,
                    evaluation = evaluation,
                    evaluation_ave = evaluation_ave,
                )

        return redirect('home')

    else:
        form = CreateReview

        # アニメタイトルのサジェスト用listの作成
        anime_title_list = []
        animemodel_list = AnimeModel.objects.all()

        for anime in animemodel_list:
            anime_title_list.append(anime.title)

    return render(request,'create_review.html',{'form' : form, 'profile' : profile, 'anime_title_list' : anime_title_list})

def update_review(request,pk):
    object = ReviewModel.objects.get (pk = pk)
    profile = ProfileModel.objects.get(user = request.user)
    review_title = object.review_title
    review_title += '\n'
    
    if request.method == 'POST':
        content_split = request.POST.get('review_content').splitlines()  # レビュー内容を改行ごとにリスト化
        object.review_title = content_split[0]  # 1行目をレビュータイトルとして保存
        content_split.pop(0)  # レビュー内容の1行目を削除(タイトルを削除)

        # ネタバレの有無による
        if request.POST.get('spoiler') == '1':
            content_split.insert(0,'※ネタバレを含む')  # 1行目にネタバレを含むを挿入
        
        object.review_content = '\r\n'.join(content_split)
        str_values = [request.POST.get('val1'),request.POST.get('val2'),request.POST.get('val3'),request.POST.get('val4'),request.POST.get('val5')]
        object.evaluation_value = '/'.join(str_values)
        int_values = [int(n) for n in str_values]
        object.evaluation_value_ave = sum(int_values)/5
        object.save()
        return redirect('review_detail', pk = pk)

    return render(request, 'update_review.html', {'object' : object, 'profile' : profile, 'review_title' : review_title})

def delete_review(request,pk):
    ReviewModel.objects.get(pk = pk).delete()  # pkから取得し、削除
    profile_id = ProfileModel.objects.get(user = request.user)  # redirect用のidを取得
    return redirect('profile', pk = profile_id.id)

def review_detail(request,pk):
    review = ReviewModel.objects.get(pk = pk)  # reviewを取得
    profile = ProfileModel.objects.get(user = request.user)  # profileを取得

    # レビュー者のその他の投稿をランダムで3つ抽出
    review_list = ReviewModel.objects.filter(user = review.user).order_by('?')[:3]

    # レビューに対するコメントを取得
    comment_list = Comment.objects.filter(review__id = pk).order_by('-created_at')
    reply_list = ReplyComment.objects.filter(comment__review__id = pk).order_by('created_at')

    # アクセスと同時にAccessReviewおよびCounterを更新
    if review.user != request.user:
        if not AccessReview.objects.filter(user = request.user).filter(review = review).exists():
            AccessReview.objects.create(user = request.user, review = review)  # AccessReviewの更新

            # レビューのジャンルをカウントする
            counter = Counter.objects.get(user = request.user)  # 訪問者のCounterを取得
            genre_counter = counter.counter

            anime = review.anime
            genre_num = genre(anime)

            for i in range(len(genre_counter)):
                if genre_num == i:
                    genre_counter[i-1] += 1

            counter.counter = genre_counter
            counter.save()

    return render(request, 'review_detail.html', {
        'review' : review,
        'profile' : profile,
        'review_list' : review_list,
        'comment_list' : comment_list,
        'reply_list' : reply_list})

def like(request,review_id,user_id):
    like = Like.objects.filter(review = review_id, user = user_id)
    if like.count() == 0:
        Like.objects.create(
            user = request.user,
            review = ReviewModel.objects.get(pk = review_id)
        )
    else:
        like.delete()
    
    return redirect('home')


def create_comment(request,pk):
    profile = ProfileModel.objects.get(user = request.user)
    if request.method == 'POST':
        form = CreateComment(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.user = request.user
            object.review = ReviewModel.objects.get(pk = pk)
            object.save()
            return redirect('review_detail', pk = pk)
    else:
        return render(request, 'create_comment.html', {'profile' : profile})

def create_reply(request,pk):
    profile = ProfileModel.objects.get(user = request.user)
    if request.method == 'POST':
        form = CreateReply(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.user = request.user
            object.comment = Comment.objects.get (pk = pk)
            object.save()
            return redirect('review_detail', pk = object.comment.review.pk)
    else:
        return render(request, 'create_reply.html', {'profile' : profile})

def setPlt(values1,values2,label1,label2):
#######各要素の設定#########
    labels = ['Senario','Drawing','Music','Character','CV']
    angles = np.linspace(0,2*np.pi,len(labels) + 1, endpoint = True)
    rgrids = [0,1,2,3,4,5] 
    rader_values1 = np.concatenate([values1, [values1[0]]])
    rader_values2 = np.concatenate([values2, [values2[0]]])

#######グラフ作成##########
    plt.rcParams["font.size"] = 16
    fig = plt.figure(facecolor='k')
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(1,1,1,polar = True)
    ax.plot(angles, rader_values1, color = 'r', label = label1)
    ax.plot(angles, rader_values2, color = 'b', label = label2)
    cm = plt.get_cmap('Reds')
    cm2 = plt.get_cmap('Blues')
    for i in range(6):
        z = i/5
        rader_value3 = [n*z for n in rader_values1]
        rader_value4 = [n*z for n in rader_values2]
        ax.fill(angles, rader_value3, alpha = 0.5, facecolor = cm(z))
        ax.fill(angles, rader_value4, alpha = 0.5, facecolor = cm2(z))
    ax.set_thetagrids(angles[:-1]*180/np.pi,labels, fontname = 'AppleGothic', color = 'snow', fontweight = 'bold')
    ax.set_rgrids([])
    ax.spines['polar'].set_visible(False)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    ax.legend(bbox_to_anchor = (1.05,1.0), loc = 'upper left')

    for grid_value in rgrids:
        grid_values = [grid_value] * (len(labels) + 1)
        ax.plot(angles, grid_values, color = 'snow', linewidth = 0.5,)
    
    for t in range(0,5):
        ax.text(x = 0,y = t, s = t,color = 'snow')

    ax.set_rlim([min(rgrids), max(rgrids)])
    ax.set_title ('Evaluation', fontname = 'SourceHanCodeJP-Regular', pad = 20, color = 'snow')
    ax.set_axisbelow(True)

def get_image():
    buf = io.BytesIO()
    plt.savefig(buf,format = 'svg',bbox_inches = 'tight',facecolor = 'dimgrey' , transparent = True)
    graph = buf.getvalue()
    buf.close()
    return graph

def get_svg2(request,pk):
    ###レビュー者の評価###
    review = ReviewModel.objects.get(pk = pk)
    values1 = review.evaluation
    label1 = 'Reviewer_Eval'

    ###全体の平均評価###
    review_list = ReviewModel.objects.filter(anime = review.anime)
    review_count = review_list.count()
    values2_sum = [0,0,0,0,0]
    for review in review_list:
        values2_sum = np.array(values2_sum) + np.array(review.evaluation)
    values2 = [n/review_count for n in values2_sum]
    label2 = 'Reviewer_Eval_Ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

def get_svg(request,pk):
    ###########high_similarity_animeの平均評価##################
    rec_anime = AnimeModel.objects.get(pk=pk)
    review_list = ReviewModel.objects.filter(anime = rec_anime)
    count = review_list.count()
    review_values_sum = [0,0,0,0,0]
    for review in review_list:
        review_values_sum = np.array(review_values_sum) + np.array(review.evaluation)
    values1 = [n/count for n in review_values_sum]
    ###########high_similarity_animeの平均評価##################
    access_animes = []
    for ac_review in AccessReview.objects.filter(user = request.user):
        anime = ac_review.review.anime
        if anime in access_animes:
            pass
        else:
            if anime.genre == rec_anime.genre:
                access_animes.append(anime)
    
    # access_animesの評価平均を取得
    ac_evaluation_sum = [0,0,0,0,0]
    for anime in access_animes:
        reviews = ReviewModel.objects.filter(anime = anime)
        evaluation_sum = [0,0,0,0,0]

        for review in reviews:
            evaluation_sum = np.array(evaluation_sum) + np.array(review.evaluation)

        evaluation_ave = [n/reviews.count() for n in evaluation_sum]

        ac_evaluation_sum = np.array(ac_evaluation_sum) + np.array(evaluation_ave)
    
    ac_evaluation_ave = [n/len(access_animes) for n in ac_evaluation_sum]    
    values2 = ac_evaluation_ave
    
    label1 = 'Reviwer_ave'
    label2 = 'Access_ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

def genre_return(str_genre):
    genre_dict = {
        1:'SF',
        2:'ファンタジー',
        3:'コメディ',
        4:'バトル',
        5:'恋愛',
        6:'スポーツ',
        7:'青春',
        8:'戦争',
    }
    genre_list = str_genre.split('/')
    genre_index = [index for index, genre in enumerate(genre_list) if genre == '1']
    match_genre_list = [genre_dict[i+1] for i in genre_index]
    return '/'.join(match_genre_list)

def anime_rank(rec_anime):
    anime_rank = {}
    anime_list = AnimeModel.objects.all()
    for anime in anime_list:
        review_list = ReviewModel.objects.filter(anime = anime)
        review_eval_sum = 0
        for review in review_list:
            review_eval_sum += review.evaluation_ave
        try:
            anime_review_ave = review_eval_sum/review_list.count()
            anime_rank[anime.title] = anime_review_ave
        except ZeroDivisionError:
            pass
    anime_sort = sorted(anime_rank.items(), reverse=True, key = lambda x : x[1])
    ranking = [anime_sort.index(item) for item in anime_sort if rec_anime.title in item[0]]
    return ranking[0] + 1
    
def genre(anime):
    genre = {
        1:'SF',
        2:'ファンタジー',
        3:'コメディ',
        4:'バトル',
        5:'恋愛',
        6:'スポーツ',
        7:'青春',
        8:'戦争',
    }

    genre_num = [key for key, value in genre.items() if value == anime.genre]

    return genre_num[0]

