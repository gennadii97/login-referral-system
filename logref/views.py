from typing import List

from django.http import JsonResponse
from django.shortcuts import render, redirect
from profiles.models import Profile
from .forms import SignupForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import settings

# Max number of users that can be registered without referral_code
MAX_NON_REFERRAL_USERS: int = 5


def signup_view(request):
    profile_id = request.session.get('ref_profile')
    print(f'{profile_id=}')
    form = SignupForm(request.POST or None)
    context = {'form': form}

    if form.is_valid():
        if profile_id is not None:
            recommended_by_profile = Profile.objects.get(id=profile_id)
            if not recommended_by_profile:
                messages.error(request, 'Invalid referrer user')
                return render(request, 'signup.html', context)
            instance = form.save()
            registered_user = User.objects.get(id=instance.id)
            registered_profile = Profile.objects.get(user=registered_user)
            registered_profile.recommended_by = recommended_by_profile.user
            registered_profile.save()

            if recommended_by_profile:
                num_points = len(recommended_by_profile.get_recommend_profiles()) + 1
                print(f'{num_points=}')
                recommended_by_profile.distribute_points(num_points)
                print(f'{recommended_by_profile.accumulated_points=}')
        else:
            if len(Profile.objects.all()) == MAX_NON_REFERRAL_USERS:
                messages.error(request, 'Limit of non-referrer users exceeded. Ask for referral code')
                return render(request, 'signup.html', context)
            form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)

        messages.success(request, "Your account has been successfully created. We have sent a confirmation email")


        subject = "Welcome to my app!!"
        message = "Hello" + user.username + "!! \n" + "Welcome to app!! \n Thank you for visiting our website \n We have also sent you a confirmation email, please confirm your email address to activate account. \n\n Thank you"
        from_email = settings.EMAIL_HOST_USER
        to_list = [user.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        return redirect('login-view')

    return render(request, 'signup.html', context)


def main_view(request, *args, **kwargs):
    code = str(kwargs.get('ref_code'))
    try:
        profile = Profile.objects.get(code=code)
        request.session['ref_profile'] = profile.id
        print('id', profile.id)
    except:
        pass

    print(request.session.get_expiry_date())

    return render(request, 'main.html', {})


def get_leaderboard(request):
    leaders: List[Profile] = Profile.objects.all().order_by('-accumulated_points')[:10]
    return JsonResponse(
        {'leaders': [{'user': leader.user.username, 'num_points': leader.accumulated_points} for leader in leaders]})
