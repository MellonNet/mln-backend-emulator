from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from mln.models.dynamic import IntegrationMessage, get_or_none
from mln.services import message as message_service
from mln.apis import oauth_utils

@csrf_exempt
def grant_award(request):
  data = oauth_utils.parse_json_request(request)
  if type(data) is HttpResponse: return data

  access_token = oauth_utils.authenticate_request(data)
  if type(access_token) is HttpResponse: return access_token

  award = data.get("award", None)
  if not award or type(award) != int:
    return HttpResponse("Invalid or missing award", status=400)

  client = access_token.client
  integration = get_or_none(IntegrationMessage, client=client, award=award)
  if not integration:
    return HttpResponse("Could not find an integration message", status=404)

  user = access_token.user
  message_service.send_template(integration.template, integration.networker, user)

  return HttpResponse(status=200)
