from django.core.exceptions import ValidationError
from mln.models.dynamic import Webhook, WebhookType

from mln.apis.utils import *
from mln.apis.json import *

WEBHOOK_SCHEMA = {
  "webhook_url": str,
  "mln_secret": str,
  "type": str,
}

@csrf_exempt
@oauth
@post_json
@check_json(WEBHOOK_SCHEMA)
def register_webhook(data, access_token):
  url = data["webhook_url"]
  secret = data["mln_secret"]
  type_raw = data["type"]
  match type_raw:
    case "messages": type = WebhookType.MESSAGES
    case "friendships": type = WebhookType.FRIENDSHIPS
    case _: return HttpResponse("Invalid type, supported types are 'friendships' and 'messages'", status=400)
  try:
    webhook = Webhook.objects.create(
      client=access_token.client,
      access_token=access_token,
      user=access_token.user,
      secret=secret,
      url=url,
      type=type,
    )
    return JsonResponse({"webhook_id": webhook.id}, status=201)
  except ValidationError as error:
    return HttpResponse(error, status=400)

@csrf_exempt
@oauth
@only_allow("DELETE")
def delete_webhook(request, access_token, id):
  webhook = get_or_none(Webhook, id=id)
  if not webhook:
    return HttpResponse("Webhook not found", status=404)
  elif webhook.access_token != access_token:
    return HttpResponse(status=403)
  else:
    webhook.delete()
    return HttpResponse(status=204)
