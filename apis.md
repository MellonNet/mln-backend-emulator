# My Lego Network APIs

MLN supports a number of APIs, which are intended for Discord bots but can theoretically be used by any integration.

### Authentication

All requests must contain the following headers:

```text
Authorization: Bearer access_token
Api-Token: api_token
```

Where `api_token` is your bot's secret API token, and `access_token` is the token granted by the OAuth sign-in flow. For more details on that, see [Sign in with MLN](./oauth.md). If either of these headers are missing, the server will respond with `401 Unauthorized`. If either of these headers are invalid, the request will be rejected with `403 Forbidden`.

### Webhooks

Some events originate from MLN and need to be sent to your client. To receive these events, use the Webhooks API as described below. Each request takes the following: 

```js
{
  "webhook_url": string
}
```

The server will respond with `201 Created`:

```js
{
  "webhook_id": string,
  "mln_secret": string,
}
```

When the specified trigger event happens, that endpoint will receive a `POST` request with the specified payload. The `Authorization` header will have the user's access token, and the `Api-Token` will have `mln_secret`, which is guaranteed to be the same across all webhooks registered by the same client. You can use this secret to verify that the webhook is really being triggered by MLN

## Inbox

### `MessageAttachmentRequest`

```js
{
	"id": int,
  "qty": int,
},
```

### `MessageAttachmentResponse`

```js
{
  "id": int,
  "name": string,
  "qty": int,
}
```

### `MessageRequest`

```js
{
  "body_id": int,
  "attachments": [ MessageAttachmentRequest ]
}
```

### `MessageResponse`

```js
{
  "id": int,
  "sender_id": int,
  "sender_username": string,
  "body_id": int,
  "body": string,
  "attachments": [ MessageAttachmentResponse ],
  "replies": [ 
  	{
      "body_id": int,
      "body": string,
    }
  ],
}
```

### GET `/api/messages` -- Get messages

Request: May contain optional query parameter `count=n`
Response: `200 Ok` with an array of the user's most `n` recent `MessageResponse`s

### POST `/api/messages` -- Send a message

```js
{
  "recipient_id": int,
  "message": MessageRequest,
}
```

Response: `201 Created` with the new message as a `MessageResponse`
Errors: `404 User/Message/Attachment not found`, `402 Payment Required` if lacking the items

## Individual messages

### GET `/api/messages/{id}` -- Get a message

Response: `200 Ok` with a `MessageResponse`
Errors: `404 Message not found`

### DELETE `/api/messages/{id}` -- Delete a message

Response: `204 No content`
Errors: `404 Message not found`

### POST `/api/messages/{id}/reply` -- Reply to a message

Request: A `MessageRequest` object
Response: `200 Ok` with the new message as a `MessageResponse`
Errors: `404 User/Message/Attachment not found`, `402 Payment Required` if lacking the items

### POST `/api/messages/{id}/mark-read` -- Mark a message as read

Response: `204 No Content`
Errors: `404 Message not found`

## Users and Friendships

### `User`

```js
{
  "username": string,
  "href
  "rank": int,
  "friendship_status": string,  // [none, friend, pending, blocked]
  "badges": {
    "id": int,
    "name": string,
    "description": string,
    "image_url": string,
  }
}
```

### `Friendship`

```js
{
  "from_user_id": int,
  "from_username": string,
  "to_user_id": int,
  "to_username": string,
  "status": string,  // [friend, pending, blocked]
}
```

### GET `/api/users/{username}` -- Get a user's profile

Response: A `User` object
Errors: `404 User not found`

### POST `/api/users/{username}/friendship` -- Send a friend request

Response: `200 Ok` with the `Friendship` object. If the other user had sent you a friend request, this request will automatically accept it.

Errors: 

- `404 User not found` if the given username does not exist
- `402 Payment Required` if the other user is a networker and has a requirement you don't meet
- `403 Forbidden` if the other user has blocked you

### DELETE `/api/users/{username}/friendship` -- Delete a friend

Response: `204 No Content`, or `200 Ok` if there is no friendship to delete
Errors: `404 User not found`

### POST `/api/users/{username}/block` -- Block a user

Response: `204 No Content` 
Errors: `404 User not found`

## Inventory and Modules

### `ItemStack`

```js
{
  "item_id": int,
  "item_name": string,
  "qty": int,
}
```

### `ModuleHarvest`

```js
{
  "module_id": int,
  "module_name": string,
  "harvest": Item,
  "tear_down": bool,  // whether harvesting would also tear down
}
```

### GET `/api/inventory` -- Query your inventory

Response: An array of `Item` objects

### GET `/api/harvest` -- Query your potential harvest

Response: `200 Ok` with an array of `ModuleHarvest` objects describing each yield

### POST `/api/harvest` -- Harvest everything on your page

Response: `200 Ok` with an array of `ModuleHarvest` objects

### POST `/api/modules/{id}/harvest` -- Harvest just one module

Response: `200 Ok` with a `ModuleHarvest` object describing the yield
Errors: 

- `404 Module not found` if the module does not exist
- `403 Forbidden` if the module does not belong to you
- `405 Method not allowed` if the module is not harvestable 

### POST `/api/modules/{id}/setup` -- Set up a module

Response: `200 Ok` with an array of `ItemStack` objects that were consumed to set up
Errors:

- `404 Module not found` if the module cannot be found
- `403 Forbidden` if the module does not belong to you
- `405 Method not allowed` if the module cannot be set up
- `402 Payment Required` if you lack the items needed. An array of `ItemStack`s will be returned

## Webhooks

### POST `/api/webhooks/messages` -- Webhooks for new messages

Trigger: When the user receives a new message
Payload: A `Message` object 

### POST `/api/webhooks/friendships` -- Webhooks for friendships

Trigger: Another user sends a friend request, accepts or denies a request, or blocks you
Payload: A `Friendship` object

### DELETE `/api/webhooks/{id}` -- Delete a webhook

Response: `200 Ok`
Errors: `404 Webhook not found`, `403 Forbidden` if the webhook was not created by your client
