class MLNMessage:
	"""
	These are messages that can be sent to the user on certain conditions.
	They don't necessarily indicate an error within MLN, rather inform the user they need to do something different.
	Like MLNError, these IDs refer to instances of MessageBody.
	"""
	I_DONT_GET_IT = 46222

# can't change this without also changing the xml - error descriptions are clientside
class MLNError(Exception):
	"""
	An error with an error message that will be shown to the user.
	The displayed messages are actually mail messages in a hidden category.
	As such, this list of raw IDs is not completely ideal and will break when message IDs are reassigned.
	"""
	OPERATION_FAILED = 46304
	YOU_ARE_BLOCKED = 46305
	ALREADY_FRIENDS = 46307
	INVITATION_ALREADY_EXISTS = 46308
	ITEM_MISSING = 46309
	ITEM_IS_NOT_MAILABLE = 46310
	MODULE_ALREADY_SETUP = 46311
	MODULE_IS_NOT_READY = 46312
	OUT_OF_VOTES = 46313
	MLN_OFFLINE = 47570
	MEMBER_NOT_FOUND = 52256

	def __init__(self, id):
		super().__init__()
		self.id = id
