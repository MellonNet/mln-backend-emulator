"""Friend functionality handlers."""

def handle_friend_process_blocking(user, request):
	relation_id = int(request.get("friendRelationID"))
	block = request.get("block") == "true"
	if block:
		user.profile.block_friend(relation_id)
	else:
		user.profile.unblock_friend(relation_id)

def handle_friend_process_invitation(user, request):
	relation_id = int(request.get("friendRelationID"))
	accept = request.get("accept") == "true"
	user.profile.handle_friend_invite_response(relation_id, accept)

def handle_friend_remove_member(user, request):
	relation_id = int(request.get("friendRelationID"))
	user.profile.remove_friend(relation_id)

def handle_friend_send_invitation(user, request):
	invitee_name = request.get("inviteeName")
	user.profile.send_friend_invite(invitee_name)
