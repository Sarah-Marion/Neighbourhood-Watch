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
