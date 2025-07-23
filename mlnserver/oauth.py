from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt

from mln.models.dynamic import OAuthClient, OAuthCode, OAuthToken, get_or_none
from datetime import timedelta

import json
import secrets

AUTH_CODE_EXPIRY = timedelta(minutes=10)

def generate_secure_token():
  return secrets.token_urlsafe(32)

@csrf_exempt
def get_token(request):
  if request.method != "POST":
    return HttpResponse(status=404)

  body = request.body
  if not body:
    return HttpResponse("Missing body", status=400)

  data = json.loads(body)
  api_token = data.get("api_token", None)
  auth_code_raw = data.get("auth_code", None)
  if not api_token or not auth_code_raw:
    return HttpResponse("Missing API token or auth code", status=400)

  auth_code = get_or_none(OAuthCode, auth_code=auth_code_raw)
  if not auth_code:
    return HttpResponse("Unrecognized auth code", status=404)

  client = auth_code.client
  if api_token != client.client_secret:
    return HttpResponse("Invalid API token", status=401)

  elapsed_time = timezone.now() - auth_code.generated_at
  if elapsed_time > AUTH_CODE_EXPIRY:
    return HttpResponse("That auth code has already expired", status=403)

  access_token_raw = generate_secure_token()
  user = auth_code.user
  OAuthToken.objects.create(access_token=access_token_raw, user=user, client=client)
  body = {
    "access_token": access_token_raw,
    "username": user.username,
  }
  return JsonResponse(body)

class OAuthLoginView(LoginView):
  def form_valid(self, form):
    auth_code = generate_secure_token()
    user = form.get_user()
    generated_at = timezone.now()
    client_id = self.request.GET.get("client_id")
    if not client_id:
      return HttpResponse("Missing client ID", status=400)
    client = get_or_none(OAuthClient, client_id=client_id)
    if not client:
      return HttpResponse(f"Client not found: {client_id}", status=404)
    OAuthCode.objects.create(user=user, auth_code=auth_code, client=client, generated_at=generated_at)
    session_id = self.request.GET.get("session_id")
    redirect_url = client.redirect_url
    url = f"{redirect_url}?session_id={session_id}&auth_code={auth_code}"
    return HttpResponseRedirect(url)

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["oauth"] = True

    client_id = self.request.GET.get("client_id")
    if not client_id:
      context["invalid"] = "Missing client id"
      return context

    client = get_or_none(OAuthClient, client_id=client_id)
    if not client:
      context["invalid"] = f"Unknown client id: {client_id}"
      return context

    session_id = self.request.GET.get("session_id")
    if not session_id:
      context["invalid"] = "Missing session_id"
      return context

    context["client_name"] = client.client_name
    context["image_url"] = client.image_url
    return context
