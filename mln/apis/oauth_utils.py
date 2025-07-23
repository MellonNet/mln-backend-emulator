from typing import Any, Optional
import json

from django.http import HttpRequest, HttpResponse

from mln.models.dynamic import get_or_none, OAuthToken

type Json = dict[str, Any]

def parse_json_request(request: HttpRequest) -> HttpResponse | Json:
  """
  Parses a POST request and returns JSON or an error response:

  - Returns '400 Bad request' if the body is empty or not valid JSON
  - Returns '405 Method not allowed' if the request is not a POST method
  """
  if (request.method != "POST"):
    return HttpResponse(status=405)

  body = request.body
  if not body:
    return HttpResponse("Missing body", status=400)

  try:
    return json.loads(body)
  except:
    return HttpResponse("Invalid JSON", status=400)

def authenticate_request(request: HttpRequest) -> HttpResponse | OAuthToken:
  """
  Returns the OAuth access token associated with a request, or an error response

  The request must have the following headers:
  - Authorization: Bearer ACCESS_TOKEN
  - Api-Token: API_TOKEN

  May return:
  - '400 Bad request' if either header is missing, or the authorization scheme is not Bearer
  - '401 Unauthorized' if the Authorization header is missing, or either token is invalid
  """
  authorization_header = request.headers.get("Authorization")
  if not authorization_header:
    return HttpResponse(
      "Missing Authorization header",
      headers={"WWW-Authenticate": 'Bearer realm="My Lego Network"'},
      status=401
    )

  parts = authorization_header.split()
  if len(parts) != 2:
    return HttpResponse("Invalid Authorization header. Expected 'Bearer ACCESS_TOKEN", status=400)

  scheme, access_token_raw = parts
  if scheme != "Bearer":
    return HttpResponse("Invalid Authorization header. Expected 'Bearer ACCESS_TOKEN", status=400)

  access_token = get_or_none(OAuthToken, access_token=access_token_raw)
  if not access_token:
    return HttpResponse("Invalid access token", status=401)

  client = access_token.client
  api_token = request.headers.get("api_token")
  if not api_token or api_token != client.client_secret:
    return HttpResponse("Invalid or missing API token", status=401)

  return access_token
