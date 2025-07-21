# Mini-game integrations

MLN can integrate with other mini-games to grant rewards in MLN based on mini-game progress and vice-versa. The general pattern is:

1. Create a mini-game server to host Flash files and handle requests
1. Serve the flash files with a session ID cookie
1. Handle requests for rewards by checking the session ID
1. If the session has no associated user, [sign into MLN with OAuth](./oauth.md)
1. Make an API request to MLN to send the user a message with items
1. Optionally, respond to the mini-game client with rewards from MLN

Each game implements these details separately, but generally, mini-game progress is tracked with a "rank" or "award" ID, which is sent to MLN to determine what message and items should be sent.

For simplicity, each mini-game is run on its own server, hosted separately. This lets us keep things simple as most mini-game servers are very basic and can use any server stack, as opposed to being forced to integrate with MLN. This also prevents issues with MLN from affecting the mini-games and vice-versa.

In MLN's database, we keep track of which rank IDs are associated with which messages in a table per minigame. This could be simplified in the future into one table for all mini-games, but since they were developed independently, it was simpler to keep them separate.

## The Robot Chronicles

 This mini-game has several overlapping missions that correspond to different networkers on MLN:

- Lego City construction missions: [Foreman Frank](https://mylegonetwork.fandom.com/wiki/Foreman_Frank)
- Lego Agents missions: [Agent Chase](https://mylegonetwork.fandom.com/wiki/Agent_Chase)
- Lego Racers missions: [Peelie Wheelie](https://mylegonetwork.fandom.com/wiki/Peelie_Wheelie)

You can befriend each of these users without any requirements. Although the mini-game has 7 "levels", there are actually only 5 "awards" that it will send to MLN:

1. Crane Quest (City): No reward or message. Maybe we should make one up because the button appears in-game...
2. Speed Inferno Challenge (Racers): If you win, Peelie Wheelie will send you some Racing Trophies
3. Infestation (Agents): Completing this mission will have Agent Chase send you some Agent's Dossiers
4. Towing the line (City): Completing this mission will have Foreman Frank send you some Hard Hats
5. The Fall of the Robot Defeating this level will have Mayor Frictionfit send you the Keys to the City

The other two missions, Battle for the Skies and Outriders challenge, don't trigger any events in MLN. To request items, send the following request:

```js
// POST /api/robot-chronicles/award
{
  "api_token": string,
  "access_token": string,
  "award": int,  // 1, 2, 3, 4, or 5
}
```

The `api_token` and `access_token` are the values you get from setting up OAuth (see link above), and the `award` corresponds to the list above. This request will call `get_award()` which will look up the correct `RobotChroniclesMessage` and send that to the user.

## Lego City Coast Guards

This mini-game has just one associated networker: [Old Capt Joe](https://mylegonetwork.fandom.com/wiki/Old_Capt_Joe). When you beat the first level of the mini-game and he will send you the `Coast Guard Badge, Rank 1 Blueprint`. Once you have built the badge, you can befriend him. Playing through the rest of the game will grant the other badges.

To let MLN know a new rank has been earned, send the following request:

```js
// POST /api/coast-guard/rank
{
  "api_token": string,
  "access_token": string,
  "rank": int,  // 1, 2, 3, 4, or 5
}
```

The `api_token` and `access_token` are the values you get from setting up OAuth (see link above), and the `rank` corresponds to the user's in-game rank. This request will call `submit_rank()` which will look up the correct `CoastGuardMessage` and send that to the user.

## Potential API refactor

Currently, each mini-game message needs the same few fields:

- a `MessageTemplate` to send, along with any `MessageTemplateAttachment`s
- a `networker` to send the template
- a `rank`/`award` to know which message to send when

There are two tables and two API endpoints with basically the same fields. If more mini-games that follow this pattern are added in the future, it may be beneficial to consolidate them:

```python
class IntegrationMessage(models.Model):
	template = models.ForeignKey(MessageTemplate, related_name="+",n_delete=models.CASCADE)
	networker = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	progress = models.IntegerField()
	client = models.ForeignKey(OAuthClient, related_name="+", on_delete=models.CASCADE)

	def __str__(self):
		return f"{self.client.client_name}: Message #{self.progress}"
```

```js
// POST /api/integration-message
{
  "api_token": string,
  "access_token": string,
  "progress": int,
}
```

Since every access token has an associated client, the handler will be able to look up the correct `IntegrationMessage` using the provided client and progress.
