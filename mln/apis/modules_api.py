from mln.models.dynamic import ItemInfo
from mln.models.dynamic.utils import get_or_none
from mln.models.dynamic.module import Module

from .users_api import get_user_response
from .utils import csrf_exempt, only_allow, HttpResponse, JsonResponse, maybe_auth
from .json import user_response

@csrf_exempt
@maybe_auth
@only_allow("GET")
def who_has(request, user, id):
  item = get_or_none(ItemInfo, id=id)
  if not item:
    return HttpResponse(f"Could not find module with id={id}", status=404)

  modules = Module.objects.filter(item_id=id)
  ready = []
  needs_setup = []
  for module in modules:
    if module.is_clickable():
      ready.append(module)
    else:
      needs_setup.append(module)

  def respond_users(modules): return [
    get_user_response(user, module.owner)
    for module in modules
  ]

  response = {
    "ready": respond_users(ready),
    "needs_setup": respond_users(needs_setup)
  }

  return JsonResponse(response, safe=False)
