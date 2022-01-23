"""
This is the main dispatch point for the XML API requests made by the flash modules.
MLN's API is encrypted using basic XOR encryption, and then base64 encoded, presumably to deter cheaters.
Requests are all sent to the same URL, the actual request type is provided in the type attribute of the request XML element.
All responses have <response> as the root XML element, which provides exception info.
This module is responsible for decrypting requests, dispatching the requests to the appropriate handlers, rendering a response XML (if any), catching any handler exceptions and rendering exception info, encrypting the response and sending it to the client.
"""
import base64
import logging
import xml.etree.ElementTree as et

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ....models.static import MLNError
from ....templatetags.mln_utils import render_to_string_stripped
from .friend import handle_friend_process_blocking, handle_friend_process_invitation, handle_friend_remove_member, handle_friend_send_invitation
from .page import handle_page_get_new, handle_page_save_layout, handle_page_save_options
from .misc import handle_blueprint_use, handle_inventory_module_get, handle_user_get_my_avatar, handle_user_save_my_avatar, handle_user_save_my_statements
from .message import handle_message_delete, handle_message_detach, handle_message_easy_reply, handle_message_easy_reply_with_attachments, handle_message_get, handle_message_list, handle_message_send, handle_message_send_with_attachment
from .module import handle_get_module_bgs, handle_module_click, handle_module_collect_winnings, handle_module_details, handle_module_harvest, handle_module_setup, handle_module_teardown
from .module_settings import handle_module_save_settings

log = logging.getLogger(__name__)

"""
Handler registry.
Either register a handler function, or a tuple of (handler function, response template).
Handlers will be called with (django user, request root XML element).
Handlers can return a dictionary of values to pass to the response template for rendering.
Handlers can raise MLNError for a specific message to be displayed to the user.
Any other exception will result in a generic error message.
"""
handlers = {
	"BlueprintUse": handle_blueprint_use,
	"FriendProcessBlocking": handle_friend_process_blocking,
	"FriendProcessInvitation": handle_friend_process_invitation,
	"FriendRemoveMember": handle_friend_remove_member,
	"FriendSendInvitation": handle_friend_send_invitation,
	"getModuleBgs": (handle_get_module_bgs, "mln/api/xml/module/get_module_bgs.xml"),
	"InventoryModuleGet": (handle_inventory_module_get, "mln/api/xml/misc/inventory_module_get.xml"),
	"PageGetNew": (handle_page_get_new, "mln/api/xml/page/page_get_new.xml"),
	"PageSaveLayout": (handle_page_save_layout, "mln/api/xml/page/page_save_layout.xml"),
	"PageSaveOptions": handle_page_save_options,
	"MessageDelete": handle_message_delete,
	"MessageDetach": handle_message_detach,
	"MessageEasyReply": handle_message_easy_reply,
	"MessageEasyReplyWithAttachments": handle_message_easy_reply_with_attachments,
	"MessageGet": (handle_message_get, "mln/api/xml/message/message_get.xml"),
	"MessageList": (handle_message_list, "mln/api/xml/message/message_list.xml"),
	"MessageSend": handle_message_send,
	"MessageSendWithAttachment": handle_message_send_with_attachment,
	"ModuleCollectWinnings": (handle_module_collect_winnings, "mln/api/xml/module/module_collect_winnings.xml"),
	"ModuleDetails": (handle_module_details, "mln/api/xml/module/module_details.xml"),
	"ModuleExecute": (handle_module_click, "mln/api/xml/module/module_click.xml"),
	"ModuleHarvest": handle_module_harvest,
	"ModuleSaveSettings": (handle_module_save_settings, "mln/api/xml/module/module_save_settings.xml"),
	"ModuleSetup": handle_module_setup,
	"ModuleVote": (handle_module_click, "mln/api/xml/module/module_click.xml"),
	"ModuleTeardown": handle_module_teardown,
	"UserGetMyAvatar": (handle_user_get_my_avatar, "mln/api/xml/misc/user_get_my_avatar.xml"),
	"UserSaveMyAvatar": handle_user_save_my_avatar,
	"UserSaveMyStatements": handle_user_save_my_statements,
}

@csrf_exempt
def webservice(request):
	data = _decrypt(request.POST["input"])
	out = _webservice_unencrypted(request.user, data)
	out = out.encode()
	out = _encrypt(out)
	return HttpResponse(out)

def _webservice_unencrypted(user, data):
	log.debug(data)
	xml_request = et.fromstring(data)
	assert xml_request.tag == "request"
	request_type = xml_request.get("type")

	log.info("Request type %s", request_type)

	template = None
	extra_context = None
	error_msg = None

	try:
		if request_type not in handlers:
			raise RuntimeError("Request type is unhandled!")
		handler = handlers[request_type]
		if isinstance(handler, tuple):
			handler, template = handler
		extra_context = handler(user, xml_request)
	except MLNError as e:
		error_msg = e.id
	except Exception as e:
		log.exception("Error in handler for %s", request_type)
		error_msg = MLNError.OPERATION_FAILED

	context = {"request_type": request_type, "error_msg": error_msg}
	if template is not None:
		if extra_context is not None:
			context.update(extra_context)
	else:
		template = "mln/api/xml/base.xml"
	out = render_to_string_stripped(template, context)

	log.debug(out)
	return out

ENCRYPTION_KEY = b"0e0 t00e0-0 i etiaonmld"

def _xor(data, key=ENCRYPTION_KEY):
	res = bytearray(len(data))
	for i in range(len(data)):
		res[i] = data[i] ^ key[i % len(key)]
	return res

def _decrypt(data):
	return _xor(base64.b64decode(data))

def _encrypt(data):
	return base64.b64encode(_xor(data))
