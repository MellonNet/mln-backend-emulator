from typing import Any, Optional
import json

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse

from mln.models.dynamic import get_or_none, OAuthToken

type Json = dict[str, Any]

def parse_json_request(request: HttpRequest) -> HttpResponse | Json:
  if (request.method != "POST"):
    return HttpResponse(status=405)

  body = request.body
  if not body:
    return HttpResponse("Missing body", status=400)

  try:
    return json.loads(body)
  except:
    return HttpResponse("Invalid JSON", status=400)

def authenticate_request(data: Json) -> HttpResponse | User:
  access_token_raw: Optional[Any] = data.get("access_token")
  if not access_token_raw or type(access_token_raw) is not str:
    return HttpResponse("Invalid or missing access token", status=400)

  access_token = get_or_none(OAuthToken, access_token=access_token_raw)
  if not access_token:
    return HttpResponse("Invalid access token", status=403)

  client = access_token.client
  api_token = data.get("api_token")
  if not api_token or api_token != client.client_secret:
    return HttpResponse("Invalid or missing API token", status=401)

  return access_token.user
