from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpRequest

from mln.models.dynamic import get_or_none
from mln.models.static import RobotChroniclesMessage

from . import oauth_api
from . import message as message_service

valid_awards = [1, 2, 3, 4, 5]

@csrf_exempt
def get_award(request: HttpRequest):
  data = oauth_api.parse_json_request(request)
  if type(data) is HttpResponse: return data

  user = oauth_api.authenticate_request(data)
  if (type(user)) is HttpResponse: return user

  award = data.get("award")
  if not award or type(award) is not int or award not in valid_awards:
    return HttpResponse("Invalid or missing award", status=400)

  message = get_or_none(RobotChroniclesMessage, award=award)
  if not message:
    return HttpResponse("Could not find message template", status=500)

  message_service.send_template(
    template=message.template,
    sender=message.networker,
    recipient=user,
  )

  return HttpResponse(status=200)
