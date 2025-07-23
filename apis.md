# My Lego Network APIs

MLN supports a thorough REST API that is intended for modern clients. The Flash frontend is limited to using an older, XML-based API.

### Authentication

All requests must contain the following headers:

```text
Authorization: Bearer access_token
Api-Token: api_token
```

Where `api_token` is your bot's secret API token, and `access_token` is the token granted by the OAuth sign-in flow. For more details on that, see [Sign in with MLN](./oauth.md).

### Webhooks

Some events originate from MLN and need to be sent to your client. To receive these events, use the Webhooks API as described below. When the specified trigger event happens, that endpoint will receive a `POST` request with the specified payload. The `Authorization` header will have the user's access token, and the `Api-Token` will have the `mln_secret` you provide when you register the webhook. You can use this secret to verify that the webhook is really being triggered by MLN

## Inbox

### `AttachmentRequest`

```js
{
  "item_id": int,
  "qty": int,
},
```

### `AttachmentResponse`

```js
{
  "item_id": int,
  "name": string,
  "qty": int,
}
```

### `MessageRequest`

```js
{
  "body_id": int,
  "attachment": AttachmentRequest | null,
}
```

### `MessageBody`

```js
{
  "id": int,
  "subject": string,
  "text": string,
}
```

### `MessageResponse`

```js
{
  "id": int,
  "sender_id": int,
  "sender_username": string,
  "body": MessageBody,
  "is_read": bool,
  "attachments": [ AttachmentResponse ],
  "replies": [ MessageBody ]
}
```

### GET `/api/messages` -- Get messages

Request: May contain optional query parameter `count=n`
Response: `200 Ok` with an array of the user's most `n` recent `MessageResponse`s

### POST `/api/messages` -- Send a message

```js
{
  "recipient": string,
  "message": MessageRequest,
}
```

Response: `201 Created` with the new message as a `MessageResponse`
Errors:

- `404 Not found` if the recipient, message body, or any attachment cannot be found
- `402 Payment Required` if you lack the items in the attachments
- `403 Forbidden` if you are not friends with the user, or have been blocked by them

## Individual messages

### GET `/api/messages/{id}` -- Get a message

Response: `200 Ok` with a `MessageResponse`
Errors: `404 Message not found`, `403 Forbidden` if not your message

### DELETE `/api/messages/{id}` -- Delete a message

Response: `204 No content`
Errors: `404 Message not found`, `403 Forbidden` if not your message

### POST `/api/messages/{id}/reply` -- Reply to a message

Request: A `MessageRequest` object
Response: `200 Ok` with the new message as a `MessageResponse`
Errors: `404 User/Message/Attachment not found`, `402 Payment Required` if lacking the items

### POST `/api/messages/{id}/mark-read` -- Mark a message as read

Response: `204 No Content`
Errors: `404 Message not found`

## Users and Friendships

### `Badge`

```js
{
  "id": int,
  "name": string,
}
```

### `User`

```js
{
  "username": string,
  "page_url": string,
  "rank": int,
  "is_networker": bool,
  "friendship_status": string,  // [none, friend, pending, blocked]
  "badges": [ Badge ]
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

Response: `204 No Content`, even if the user was not your friend
Errors: `404 User not found`, `403 Forbidden` if the user blocked you

### POST `/api/users/{username}/block` -- Block a user

Response: `204 No Content`
Errors: `404 User/Friendship not found`,

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

### POST `/api/webhooks` -- Register a webhook

```js
{
  "webhook_url": string,
  "mln_secret": string,  // anything
  "type": string,  // one of "messages", "friendships"
}
```

Response: `201 Created`:

```js
{
  "webhook_id": string,
}
```

The `type` determines when the webhook will be called:

- `messages`: When the user receives a new message. Payload: A `Message` object
- `friendships`: When another user sends a friend request, accepts or denies a request, or blocks you
  Payload: A `Friendship` object

See [the section on webhooks](#Webhooks) for more details

### DELETE `/api/webhooks/{id}` -- Delete a webhook

Response: `204 No Content`
Errors: `404 Webhook not found`, `403 Forbidden` if the webhook was not created by your client
