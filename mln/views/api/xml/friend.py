from ....services.friend import block_friend, handle_friend_invite_response, remove_friend, send_friend_invite, unblock_friend

def handle_friend_process_blocking(user, request):
	relation_id = int(request.get("friendRelationID"))
	block = request.get("block") == "true"
	if block:
		block_friend(user, relation_id)
	else:
		unblock_friend(user, relation_id)

def handle_friend_process_invitation(user, request):
	relation_id = int(request.get("friendRelationID"))
	accept = request.get("accept") == "true"
	handle_friend_invite_response(user, relation_id, accept)

def handle_friend_remove_member(user, request):
	relation_id = int(request.get("friendRelationID"))
	remove_friend(user, relation_id)

def handle_friend_send_invitation(user, request):
	invitee_name = request.get("inviteeName")
	send_friend_invite(user, invitee_name)
