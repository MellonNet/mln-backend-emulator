import json
import secrets

from datetime import timedelta

from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from mln.models.dynamic import OAuthClient, OAuthCode, OAuthToken, get_or_none
from mln.apis.utils import oauth_only, post_json, check_json

AUTH_CODE_EXPIRY = timedelta(minutes=10)

def generate_secure_token():
  return secrets.token_urlsafe(32)


OAUTH_TOKEN_SCHEMA = {
  "api_token": str,
  "auth_code": str,
}

@csrf_exempt
@post_json
@check_json(OAUTH_TOKEN_SCHEMA)
def get_token(data):
  api_token = data["api_token"]
  auth_code_raw = data["auth_code"]

  auth_code = get_or_none(OAuthCode, auth_code=auth_code_raw)
  if not auth_code:
    return HttpResponse("Unrecognized auth code", status=404)

  client = auth_code.client
  if api_token != client.client_secret:
    return HttpResponse("Invalid API token", status=401)

  elapsed_time = timezone.now() - auth_code.generated_at
  if elapsed_time > AUTH_CODE_EXPIRY:
    return HttpResponse("That auth code has already expired", status=403)

  access_token_other = get_or_none(OAuthToken, auth_code=auth_code)
  if access_token_other:
    return HttpResponse("This auth code has already been redeemed", status=401)

  access_token_raw = generate_secure_token()
  user = auth_code.user
  OAuthToken.objects.create(access_token=access_token_raw, user=user, client=client, auth_code=auth_code)
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

@csrf_exempt
@oauth_only
def oauth_logout(data, access_token):
  all_tokens = list(OAuthToken.objects.filter(user=access_token.user, client=access_token.client))
  for token in all_tokens:
    token.delete()

  return HttpResponse(status=200)
