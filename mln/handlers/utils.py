"""Handler utility functions."""

def uuid_int(uuid_str):
	"""
	Original MLN uses a lot of UUID-formatted integer IDs which aren't true UUIDs, they aren't random, they're normal integers.
	Therefore this server uses integers internally and any UUIDs should be converted to integers as soon as possible using this function.
	MLN's IDs aren't actually required to be UUIDs per se, this function is purely for backwards compatibility with the original XML editorial.
	As soon as we decide to modify the XML we should change the formatting to normal integers so this function won't be necessary.
	"""
	first_sep = uuid_str.index("-")
	second_sep = uuid_str.index("-", first_sep+1)
	third_sep = uuid_str.index("-", second_sep+1)
	first_part = uuid_str[:first_sep]
	third_part = uuid_str[second_sep+1:third_sep]
	return int(first_part, 16) + (int(third_part, 16) << 24)
