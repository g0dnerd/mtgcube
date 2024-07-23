from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt


User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):

    model = User
    fields = ["name", "pronouns"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        self.request.user.save()
        return self.request.user.get_absolute_url()  # type: ignore [union-attr]

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

user_redirect_view = UserRedirectView.as_view()

@csrf_exempt
def google_login(request):
    from urllib.parse import urlparse
    url = urlparse(request.headers.get('Origin'))
    domain = url.hostname
    if url.port:
        domain += ':' + str(url.port)
    prefix = 'https://' if request.is_secure() else 'http://'
    home_page = prefix + domain if prefix not in domain else domain
    login_url = '/accounts/google/login/'
    return redirect(home_page + login_url)
