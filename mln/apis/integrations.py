from mln.models.dynamic import IntegrationMessage, get_or_none
from mln.services import message as message_service
from mln.apis.utils import *

@csrf_exempt
@oauth
@post_json
def grant_award(data, access_token):
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
