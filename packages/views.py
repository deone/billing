from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect

from billing.decorators import must_be_individual_user

from accounts.models import Radcheck
from accounts.helpers import md5_password
from utils import save_subscription, check_subscription

from .forms import PackageSubscriptionForm
from .models import Package, InstantVoucher

@ensure_csrf_cookie
def insert_stub(request):
    """ This view is strictly for testing. """
    response = {}
    if request.method == 'POST':
        package = Package.objects.create(package_type=request.POST['package_type'],
            speed=request.POST['speed'], volume=request.POST['volume'], price=request.POST['price'])
        package.__dict__.pop("_state")
        response.update({'code': 200, 'result': package.__dict__})
    else:
        response.update({'status': 'ok'})

    return JsonResponse(response)

@ensure_csrf_cookie
def delete_stub(request):
    """ This view is strictly for testing. """
    response = {}
    if request.method == 'POST':
        package = Package.objects.get(pk=request.POST['package_id'])
        package.delete()
        response.update({'code': 200})
    else:
        response.update({'status': 'ok'})

    return JsonResponse(response)

@ensure_csrf_cookie
def packages(request):
    response = {}
    packages = []
    for p in Package.objects.all():
        string = p.package_type + ' ' + p.speed + ' Mbps ' + str(p.price) + ' GHS'
        tup = (p.pk, string)
        packages.append(tup)
    response.update({'code': 200, 'results': list(packages)})
    return JsonResponse(response)

@ensure_csrf_cookie
def insert_vouchers(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        package_id = request.POST['package_id']

        radcheck = Radcheck.objects.create(username=username,
                                    attribute='MD5-Password',
                                    op=':=',
                                    value=md5_password(password))
        package = Package.objects.get(pk=package_id)

        InstantVoucher.objects.create(radcheck=radcheck, package=package)

    return JsonResponse({'status': 'ok'})

@login_required
@must_be_individual_user
def create_subscription(request, package_pk):
    token = request.GET.get('token', None)

    package = Package.objects.get(pk=package_pk)
    radcheck = Radcheck.objects.get(username__exact=request.user.username)
    start = check_subscription(radcheck=radcheck)

    subscription = save_subscription(radcheck, package, start, amount=None, balance=None, token=token)
    
    # http://154.117.8.19:7700/captive/?
    # login_url=https%3A%2F%2Fn110.network-auth.com%2Fsplash%2Flogin%3Fmauth%3DMMsZpCSqxZ2L2rm632E6xwH20P36xhfNn1a0K4ODxSRHepGkUFID26iKjWQNhzfJNYZtdXOTzitDBKGRfisryvnyqiB-BT4kiowWn1jqTyZbZV93r7i-kBxth1AgwUEAJi_g8fJbJZzRgLbD9N4rlozNnYFd2xiXT8h-vPUSoYJEQBGWomOiwSMA%26continue_url%3Dhttp%253A%252F%252Fgoogle.com%252F
    # &continue_url=http%3A%2F%2Fgoogle.com%2F
    # &ap_mac=00%3A18%3A0a%3Af2%3Ade%3A20
    # &ap_name=Spectra-HQ-NOC
    # &ap_tags=office-accra+recently-added
    # &client_mac=4c%3Aeb%3A42%3Ace%3A6c%3A3d
    # &client_ip=10.8.0.78
    captive_url = '%s?login_url=%s&continue_url=%s&ap_mac=%s&ap_name=%s&ap_tags=%s&client_mac=%s&client_ip=%s' % (
        reverse('captive'), 
        request.session['login_url'], 
        request.session['continue_url'],
        request.session['ap_mac'],
        request.session['ap_name'],
        request.session['ap_tags'],
        request.session['client_mac'],
        request.session['client_ip']
        )

    messages.success(request, 
        "%s%s" % ('Package purchased successfully. You may ', "<a href=" + captive_url + ">log in</a> to browse."))
    return redirect('packages:buy')

@login_required
@must_be_individual_user
def buy_package(request):
    context = {}
    packages = [(p.id, p) for p in Package.objects.all()]
    if request.method == "POST":
        form = PackageSubscriptionForm(request.POST, user=request.user, packages=packages)
        if form.is_valid():
            form.save()
            messages.success(request, 'Package purchased successfully.')
            return redirect('packages:buy')
    else:
        form = PackageSubscriptionForm(user=request.user, packages=packages)

    context.update(
        {
          'form': form,
          'speed_map': settings.SPEED_NAME_MAP,
          'volume_map': settings.VOLUME_NAME_MAP
          }
        )

    return render(request, 'packages/buy_package.html', context)