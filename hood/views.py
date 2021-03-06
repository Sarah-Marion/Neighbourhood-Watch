from django.shortcuts import render, redirect, HttpResponseRedirect
from .forms import SignUpForm, LoginForm, ProfileUpdateForm, NewPostForm, HoodForm
import json
import requests
from .models import Profile, Hood, Location, Business, News
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.forms.models import inlineformset_factory
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from googlemaps import Client, convert
from django.conf import settings
from .decorators import user_belongs_to_hood


# Create your views here.
def signup(request):
    current_user = request.user
    # if current_user.is_authenticated():
    #     return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your Neighbourhood Watch Account'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def account_activation_sent(request):
    current_user = request.user
    if current_user.is_authenticated():
        return HttpResponseRedirect('/')
    return render(request, 'registration/activation_complete.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('logout')
    else:
        return render(request, 'registration/account_activation_invalid.html')


@login_required
def select_hood(request):
    form = HoodForm()
    user = Profile.objects.get(profile_owner=request.user)
    user_has_hood = user.profile_hood

    if request.method == 'POST' and 'hood_name' in request.POST is not None:

        form = HoodForm(request.POST)
        location_id = request.POST.get('hood_location')
        hood_id = request.POST.get('hood_name')

        hood = Hood.objects.get(id=hood_id)

        user.profile_hood = hood
        user.save()

        return redirect(index)

    return render(request, 'hood/select-hood.html', {'form': form, 'user_has_hood': user_has_hood})


@login_required
def load_hood(request):
    if request.method == "GET" and 'hood_location' in request.GET and request.is_ajax():
        location_id = request.GET.get('hood_location')
        hoods = Hood.objects.filter(hood_location=location_id)
    return render(request, 'hood/hood_dropdown.html', {'hoods': hoods})


@login_required
@user_belongs_to_hood
def index(request):

    google_key = settings.GOOGLE_API
    geocode_url = settings.GEOCODE_URL
    gmaps = Client(key=google_key)

    profile_instance = Profile.objects.get(id=request.user.id)
    hood_instance = Hood.objects.filter(hood_name=profile_instance.profile_hood.hood_name)

    place = profile_instance.profile_hood.hood_location.loc_name

    place = place.strip().replace(" ", "+")
    response = requests.get(geocode_url.format(place, google_key))

    general_address = response.json()
    address = general_address['results'][0]['geometry']['location']


    nearby_police_results = gmaps.places_nearby(location=address, keyword='police',
                                                language='en-US', open_now=True,
                                                rank_by='distance', type='police')

    nearby_hospital_results = gmaps.places_nearby(location=address, keyword='hospital',
                                                  language='en-US', open_now=True,
                                                  rank_by='distance', type='hospital')


    hood_news = News.objects.filter(news_hood=hood_instance)

    return render(request, 'index.html', {'hood_news': hood_news,  'police': nearby_police_results, 'hospitals': nearby_hospital_results})


@login_required
def post(request):
    profile_instance = Profile.objects.get(id=request.user.id)
    place = profile_instance.profile_hood.pk
    place = Hood.objects.get(id=place)

    if request.method == 'POST':
        form = NewPostForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.news_created_by = profile_instance
            news.news_hood = place
            news.save()
        return redirect(index)
    else:
        form = NewPostForm()

    return render(request, 'hood/news.html', {"form": form})


@login_required
def profile(request):
    current_user = request.user
    profile_details = User.objects.get(id=request.user.id)

    user = User.objects.get(id=current_user.id)

    update_form = ProfileUpdateForm(instance=user)

    ProfileInlineFormset = inlineformset_factory(
        User, Profile, fields=('profile_photo', 'profile_id',))
    formset = ProfileInlineFormset(instance=user)

    if current_user.is_authenticated() and current_user.id == user.id:
        if request.method == "POST":
            update_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            formset = ProfileInlineFormset(request.POST, request.FILES, instance=user)

            if update_form.is_valid():
                updated_user = update_form.save(commit=False)
                formset = ProfileInlineFormset(request.POST, request.FILES, instance=current_user)

                if formset.is_valid():
                    updated_user.save()
                    formset.save()
                    return redirect(index)

    return render(request, 'profile.html', {'profile_data': profile_details, "formset": formset, 'updated_user': update_form})



@login_required
def new_location(request):

    if request.method == 'POST' and 'hood-name' in request.POST:
        hood_name = request.POST.get('hood-name')
        hood_location = request.POST.get('hood-location')

        user_profile = Profile.objects.get(id=request.user.id)

        new_location = Location(loc_name=hood_location)
        new_location.save()

        new_hood = Hood(hood_name=hood_name, hood_location=new_location, hood_admin=user_profile)
        new_hood.save()

        user_profile.update_profile_hood(user_profile.id, new_hood)

        return redirect('profile')

    return render(request, 'hood/new-location.html')


@login_required
@user_belongs_to_hood
def new_business(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST)
        profile_instance = Profile.find_profile_by_userid(request.user.id)
        profile_instance_hood = profile_instance.profile_hood
        if form.is_valid():
            new_bs = form.save(commit=False)
            new_bs.business_owner = profile_instance
            new_bs.business_hood = profile_instance_hood
            new_bs.save()
            messages.success(request, 'Business Added successfully')
            return redirect(manage_business)
    else:
        form = BusinessForm()

    return render(request, 'business/new-business.html', {'form': form})


@login_required
@user_belongs_to_hood
def update_business(request, business_id):
    if request.method == 'POST':
        instance = get_object_or_404(Business, id=business_id)
        form = BusinessForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business updated successfully')
    return redirect(manage_business)


@login_required
@user_belongs_to_hood
def manage_business(request):
    profile_instance = Profile.find_profile_by_userid(request.user.id)
    businesses = Business.objects.filter(business_owner=profile_instance).all()
    return render(request, 'business/manage-business.html', {'businesses': businesses})


@login_required
@user_belongs_to_hood
def all_business(request):
    profile_instance = Profile.objects.get(id=request.user.id)
    hood_instance = Hood.objects.filter(hood_name=profile_instance.profile_hood.hood_name)

    business = Business.objects.filter(business_hood=hood_instance)
    return render(request, 'business/view-business.html', {'businesses': business})


@login_required
def check_location_exists(request):
    if request.method == 'POST' and request.is_ajax():
        set_hood = request.POST.get('hood-name').strip()
        location_exists = Hood.objects.filter(hood_name__iexact=set_hood).all()
        user_profile = Profile.find_profile_by_userid(request.user.id)
        user_is_hood_admin = Hood.objects.filter(hood_admin=user_profile)

        if location_exists:
            status = 'exists'

        if not location_exists:
            status = 'not exist'

        if user_is_hood_admin:
            status = 'admin'

        status = json.dumps(status)

        return HttpResponse(status, content_type='application/json')


@login_required
def retrieve_business_info(request):
    if request.method == "GET" and 'business_id' in request.GET and request.is_ajax():
        business_pk = request.GET.get('business_id')
        found_bs = Business.objects.get(id=business_pk)

        form = BusinessForm(initial={'business_name': found_bs.business_name, 'business_email': found_bs.business_email,
                                     'business_category': found_bs.business_category, 'business_description': found_bs.business_description})
        return render(request, 'business/retrive-business.html', {'form': form, 'bs_id': business_pk})

    if request.method == "GET" and 'b_id' in request.GET and request.is_ajax():
        business_pk = request.GET.get('b_id')
        Business.objects.filter(id=business_pk).delete()
        status = 'deleted'
        return redirect(manage_business)



