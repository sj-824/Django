from django.shortcuts import render, redirect, get_list_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView)
from .forms import LoginForm, UserCreateForm, CreateProfile, CreateReview, CreateComment, CreateReply
from .models import User, ProfileModel, ReviewModel, Counter, AnimeModel, AccessReview, Comment, ReplyComment
import requests
import matplotlib.pyplot as plt
import numpy as np
from django.http import HttpResponse
import io
import math
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
        form = CreateProfile(request.POST)
        Counter.objects.create(username = request.user,genre_counter = '0/0/0/0/0/0/0/0')
        if form.is_valid():
            object = form.save(commit = False)
            object.username = request.user
            object.save()
            return redirect('home')
    else:
        form = CreateProfile
    return render(request,'create_profile.html',{'form' : form})

def home(request):
    review_list = ReviewModel.objects.all().order_by('-post_date')
    profile = ProfileModel.objects.get(username = request.user)

    # おすすめアニメの表示
    counter = Counter.objects.get(username = request.user)  
    genre_counter = counter.genre_counter.split('/')             # 各ジャンルに該当するレビューへのアクセス数をリスト化
    int_genre_counter = [int(n) for n in genre_counter]          # アクセス数をintへ変換
    max_genre = int_genre_counter.index(max(int_genre_counter))  # 最もアクセス数の高いジャンルのindexを取得

    anime_list = []
    if AccessReview.objects.filter(access_name = request.user).exists():                              # アニメが登録されている=True
        # 各アニメのジャンルとアクセス数の高いジャンルが一致したアニメをリスト化
        for animemodel in AnimeModel.objects.all():              
            anime_genre = animemodel.anime_genre.split('/')
            if anime_genre[max_genre] == '1':                    
                anime_list.append(animemodel.anime_title)
        anime_list = AnimeModel.objects.filter(anime_title__in = anime_list)  

        # アクセスしたアニメの平均レビュー評価
        access_review_list = AccessReview.objects.filter(access_name = request.user).filter(review__anime_title__in = anime_list)  # ジャンルの一致したアニメの内アクセスしたアニメの平均レビュー評価を取得
        access_anime_title = []

        # アクセスしたレビューのアニメを抽出
        for access_review in access_review_list:
            if access_review.review.anime_title not in access_anime_title:  # 同一アニメのレビューを観ている場合、重複を防ぐ
                access_anime_title.append(access_review.review.anime_title)

        # アクセスしたレビューのアニメの平均レビュー評価を抽出
        for access_anime in access_anime_title:
            review_match_list= ReviewModel.objects.filter(anime_title = access_anime)
            review_values_sum = [0,0,0,0,0]
            review_values_ave_sum = [0,0,0,0,0]

            for review_match in review_match_list:
                review_values = review_match.evaluation_value.split('/')
                int_review_values = [int(n) for n in review_values]
                review_values_sum = np.array(review_values_sum) + np.array(int_review_values)

            review_values_ave = [n/review_match_list.count() for n in review_values_sum]
            review_values_ave_sum = np.array(review_values_ave_sum) + np.array(review_values_ave)

        review_values_ave_sum_ave = [n/len(access_anime_title) for n in review_values_ave_sum]
        
        # 各アニメの平均評価
        anime_dict = {}
        for anime in anime_list:
            anime_review_list = ReviewModel.objects.filter(anime_title = anime)
            count = anime_review_list.count()
            anime_values_sum = [0,0,0,0,0]

            for review in anime_review_list:
                anime_values = review.evaluation_value.split('/')
                int_anime_values = [int(n) for n in anime_values]
                anime_values_sum = np.array(anime_values_sum) + np.array(int_anime_values)

            anime_values_ave = [n/count for n in anime_values_sum]
            anime_dict[anime.anime_title] = anime_values_ave

        # 最も平均評価が類似したアニメを抽出
        anime_similarity = {}  # key:アニメ名,value:類似値 (ex: 'Anime' : √(x2-x1)^2)

        for title, values in anime_dict.items():
            value_sub = np.array(review_values_ave_sum_ave) - np.array(values)  # 差分を取得
            value_sub_sqr = map(lambda x : x**2, value_sub)                     # 各差分値を2乗
            anime_similarity[title] = math.sqrt(sum(value_sub_sqr))             # 各差分値の2乗の合計の平方根を取得
        anime_title = min(anime_similarity,key = anime_similarity.get)
        high_similarity_anime = AnimeModel.objects.get(anime_title = anime_title)
        str_genre = high_similarity_anime.anime_genre
        top_anime_genre = genre_return(str_genre)
        rank = anime_rank(high_similarity_anime.anime_title)
        trend_anime_review = ReviewModel.objects.filter(anime_title = high_similarity_anime)
        review_count = trend_anime_review.count()

        ############high_similarity_animeの平均値を取得############
        # anime_dictから対象のアニメの評価値を取得
        value_ave_item = anime_dict[high_similarity_anime.anime_title]
        value_ave = f'{sum(value_ave_item)/len(value_ave_item):.1f}'
        return render(request,'home.html',{
            'review_list' : review_list, 
            'profile' : profile, 
            'high_similarity_anime' : high_similarity_anime, 
            'top_anime_genre' : top_anime_genre, 
            'rank' : rank,
            'review_count' : review_count,
            'value_ave' : value_ave})
    return render(request,'home.html',{'review_list' : review_list, 'profile' : profile})

def profile(request,pk):
    profile = ProfileModel.objects.get(pk = pk)
    review_list = ReviewModel.objects.filter(username = profile.username).order_by('-post_date')
    review_num = ReviewModel.objects.filter(username = profile.username).exists()
    if review_list.exists():
        return render(request, 'profile.html', {'profile' : profile, 'review_list' : review_list,'review_num' : review_num})
    else:
        review_num = 0
        context = '投稿レビューはありません'
        return render(request, 'profile.html',{'profile' : profile, 'context' : context, 'review_num' : review_num})

def create_review(request):
    profile = ProfileModel.objects.get(username = request.user)  # profileを取得

    # 投稿するアニメが過去にレビューされているか取得
    if 'search' in request.POST:  # search-btnが押された場合
        anime_title = request.POST.get('anime_title')
        try:
            anime = AnimeModel.objects.get(anime_title = anime_title)
            return render(request,'create_review.html',{'anime_title' : anime_title, 'profile' : profile})
        except AnimeModel.DoesNotExist:
            AnimeModel.objects.create(anime_title = anime_title)
            context = 'そのアニメに関する投稿はまだないため、入力してください'
            return render(request, 'create_review.html', {'anime_title' : anime_title,'context' : context, 'profile' : profile})

    if 'post' in request.POST:
        anime = request.POST.get('anime_title')
        past_post = ReviewModel.objects.filter(username = request.user).filter(anime_title__anime_title = anime)
        if past_post.exists():
            context = '過去にこのアニメについて投稿しています'
            return render(request, 'create_review.html', {'context' : context, 'profile' : profile})
        form = CreateReview(request.POST)
        if form.is_valid():
            object = form.save(commit = False)
            object.username = request.user
            object.nickname = ProfileModel.objects.get(username = request.user)
            object.anime_title = AnimeModel.objects.get(anime_title = request.POST.get('anime_title'))
            content_split = request.POST.get('review_content').splitlines()
            object.review_title = content_split[0]
            content_split.pop(0)
            if request.POST.get('spoiler') == '1':
                content_split.insert(0,'※ネタバレを含む')
            object.review_content = '\r\n'.join(content_split)
            object.evaluation_value = request.POST.get('val1') + '/' + request.POST.get('val2') + '/' + request.POST.get('val3') + '/' + request.POST.get('val4') + '/' + request.POST.get('val5')
            object.evaluation_value_ave = (int(request.POST.get('val1')) + int(request.POST.get('val2')) + int(request.POST.get('val3')) + int(request.POST.get('val4')) + int(request.POST.get('val5')))/5
            object.save()
            #############AnimeModelへのジャンル追加###########
            anime_title = request.POST.get('anime_title')
            animemodel = AnimeModel.objects.get(anime_title = anime_title)
            anime_genre = animemodel.anime_genre.split('/')
            i = int(request.POST.get('anime_genre')) -1
            if anime_genre[i] == '0':
                anime_genre[i] = '1'
                animemodel.anime_genre = '/'.join(anime_genre)
                print(animemodel.anime_genre)
                animemodel.save()
            #############AnimeModelへのジャンル追加###########
            return redirect('home')
    else:
        form = CreateReview

        anime_title_list = []
        animemodel_list = AnimeModel.objects.all()

        for anime in animemodel_list:
            anime_title_list.append(anime.anime_title)

    return render(request,'create_review.html',{'form' : form, 'profile' : profile, 'anime_title_list' : anime_title_list})

def review_detail(request,pk):
    review = ReviewModel.objects.get(pk = pk)  # reviewを取得
    profile = ProfileModel.objects.get(username = request.user)  # profileを取得

    # レビュー者のその他の投稿をランダムで3つ抽出
    review_list = ReviewModel.objects.filter(username = review.username).order_by('?')[:3]

    # レビューに対するコメントを取得
    comment_list = Comment.objects.filter(review__id = pk).order_by('-created_at')
    reply_list = ReplyComment.objects.filter(comment__review__id = pk).order_by('created_at')

    # アクセスと同時にAccessReviewおよびCounterを更新
    if review.username != request.user:
        if not AccessReview.objects.filter(access_name = request.user).filter(review = review).exists():
            AccessReview.objects.create(access_name = request.user, review = review)  # AccessReviewの更新

            # レビューのジャンルをカウントする
            counter = Counter.objects.get(username = request.user)  # 訪問者のCounterを取得
            genre_counter = counter.genre_counter.split('/')
            int_genre_counter = [int(n) for n in genre_counter]

            for i in range(len(genre_counter)):
                if review.anime_genre == int(i + 1):
                    int_genre_counter[i] += 1

            genre_counter = [str(n) for n in int_genre_counter]
            counter.genre_counter = '/'.join(genre_counter)
            counter.visited_review = review
            counter.save()

    return render(request, 'review_detail.html', {
        'review' : review,
        'profile' : profile,
        'review_list' : review_list,
        'comment_list' : comment_list,
        'reply_list' : reply_list})

def create_comment(request,pk):
    profile = ProfileModel.objects.get(username = request.user)
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
    profile = ProfileModel.objects.get(username = request.user)
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
    labels = ['シナリオ','作画','音楽','キャラクター','声優']
    angles = np.linspace(0,2*np.pi,len(labels) + 1, endpoint = True)
    rgrids = [0,1,2,3,4,5] 
    rader_values1 = np.concatenate([values1, [values1[0]]])
    rader_values2 = np.concatenate([values2, [values2[0]]])

#######グラフ作成##########
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
    ax.set_thetagrids(angles[:-1]*180/np.pi,labels,fontname = 'Source Han Code JP',color = 'snow', fontweight = 'bold')
    ax.set_rgrids([])
    ax.spines['polar'].set_visible(False)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    ax.legend(bbox_to_anchor = (1.05,1.0), loc = 'upper left')

    for grid_value in rgrids:
        grid_values = [grid_value] * (len(labels) + 1)
        ax.plot(angles, grid_values, color = 'snow', linewidth = 0.5,)
    
    for t in rgrids:
        ax.text(x = 0,y = t, s = t,color = 'snow')

    ax.set_rlim([min(rgrids), max(rgrids)])
    ax.set_title ('評価', fontname = 'Source Han Code JP', pad = 20, color = 'snow')
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
    str_values  = review.evaluation_value.split('/')
    values1 = [int(n) for n in str_values]
    label1 = 'Reviewer_Eval'

    ###全体の平均評価###
    review_list = ReviewModel.objects.filter(anime_title = review.anime_title)
    review_count = review_list.count()
    values2_sum = [0,0,0,0,0]
    for item in review_list:
        str_values = item.evaluation_value.split('/')
        int_values = [int (n) for n in str_values]
        values2_sum = np.array(values2_sum) + np.array(int_values)
    values2 = [n/review_count for n in values2_sum]
    label2 = 'Reviewer_Eval_Ave'
    setPlt(values1,values2,label1,label2)
    svg = get_image()
    plt.cla()
    response = HttpResponse(svg, content_type = 'image/svg+xml')
    return response

def get_svg(request,pk):
    ###########high_similarity_animeの平均評価##################
    anime = AnimeModel.objects.get(pk=pk)
    review_list = ReviewModel.objects.filter(anime_title = anime)
    count = review_list.count()
    review_values_sum = [0,0,0,0,0]
    for review in review_list:
        review_values = review.evaluation_value.split('/')
        int_review_values = [int(n) for n in review_values]
        review_values_sum = np.array(review_values_sum) + np.array(int_review_values)
    values1 = [n/count for n in review_values_sum]
    ###########high_similarity_animeの平均評価##################

    ###########AccessReviewの平均評価###########################
    counter = Counter.objects.get(username = request.user)
    genre_counter = counter.genre_counter.split('/')
    int_genre_counter = [int(n) for n in genre_counter]
    max_genre = int_genre_counter.index(max(int_genre_counter))
    anime_list = []
    if AnimeModel.objects.exists():
        for animemodel in AnimeModel.objects.all():
            anime_genre = animemodel.anime_genre.split('/')
            if anime_genre[max_genre] == '1':
                anime_list.append(animemodel.anime_title)
        #############ジャンルの一致したアニメを取得######################
        anime_list = AnimeModel.objects.filter(anime_title__in = anime_list)
        #############訪問したレビューの平均評価########################
        access_review_list = AccessReview.objects.filter(access_name = request.user).filter(review__anime_title__in = anime_list)
        access_anime_title = []
        for access_review in access_review_list:
            if access_review.review.anime_title not in access_anime_title:
                access_anime_title.append(access_review.review.anime_title)
        for access_anime in access_anime_title:
            review_match_list= ReviewModel.objects.filter(anime_title = access_anime)
            review_values_sum = [0,0,0,0,0]
            review_values_ave_sum = [0,0,0,0,0]
            for review_match in review_match_list:
                review_values = review_match.evaluation_value.split('/')
                int_review_values = [int(n) for n in review_values]
                review_values_sum = np.array(review_values_sum) + np.array(int_review_values)
            review_values_ave = [n/review_match_list.count() for n in review_values_sum]
            review_values_ave_sum = np.array(review_values_ave_sum) + np.array(review_values_ave)
        values2 = [n/len(access_anime_title) for n in review_values_ave_sum]
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

def anime_rank(anime_title):
    anime_rank = {}
    anime_list = AnimeModel.objects.all()
    for anime in anime_list:
        review_list = ReviewModel.objects.filter(anime_title = anime)
        review_eval_sum = 0
        for review in review_list:
            review_eval_ave = review.evaluation_value_ave
            review_eval_sum += review_eval_ave
        try:
            anime_review_ave = review_eval_sum/review_list.count()
            anime_rank[anime.anime_title] = anime_review_ave
        except ZeroDivisionError:
            break
            
        
    anime_sort = sorted(anime_rank.items(), reverse=True, key = lambda x : x[1])
    ranking = [anime_sort.index(item) for item in anime_sort if anime_title in item[0]]
    return ranking[0] + 1
    
