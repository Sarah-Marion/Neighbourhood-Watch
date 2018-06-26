from django.shortcuts import redirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from .models import Profile

def user_belongs_to_hood(function):
    def wrap(request, *args, **kwargs):
        profile = Profile.objects.get(profile_owner=request.user)
        if not profile.profile_hood_id:
            messages.info(request, 'Kindly join or create a neighbourhood to continue')
            return redirect(reverse('new_location'))
        elif not profile.profile_id:
            messages.info(request, 'Kindly input your ID number')
            return redirect(reverse('profile'))
        else:
            return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
