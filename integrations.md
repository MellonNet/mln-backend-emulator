# Mini-game integrations

MLN can integrate with other mini-games to grant awards in MLN based on mini-game progress and vice-versa. The general pattern is:

1. Create a mini-game server to host Flash files and handle requests
1. Serve the flash files with a session ID cookie
1. Handle requests for rewards by checking the session ID
1. If the session has no associated user, [sign into MLN with OAuth](./oauth.md)
1. Make an API request to MLN to send the user a message with items
1. Optionally, respond to the mini-game client with rewards from MLN

Each game implements these details separately, but generally, mini-game progress is tracked with an "award" ID, which is sent to MLN to determine what message and items should be sent.

For simplicity, each mini-game is run on its own server, hosted separately. This lets us keep things simple as most mini-game servers are very basic and can use any server stack, as opposed to being forced to integrate with MLN's Django stack. This also prevents issues with MLN from affecting the mini-games and vice-versa.

## The `IntegrationMessage` model

Each mini-game message needs the same few fields:

- a `MessageTemplate` to send, along with any `MessageTemplateAttachment`s
- a `networker` to send the template
- an `award` ID that is associated with in-game progress

That makes

```python
class IntegrationMessage(models.Model):
	template = models.ForeignKey(MessageTemplate, related_name="+",n_delete=models.CASCADE)
	networker = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	award = models.IntegerField()
	client = models.ForeignKey(OAuthClient, related_name="+", on_delete=models.CASCADE)

	def __str__(self):
		return f"{self.client.client_name}: Message #{self.award}"
```

When the user completes an achievement in the mini-game, its server should make the following request:

```http
POST /api/integration-message HTTP/1.1
Authorization: Bearer ACCESS_TOKEN
Api-Token: API_TOKEN

{
  "award": int,
}
```

Since every access token has an associated client, the handler will be able to look up the correct `IntegrationMessage` using the provided access token and progress.

## The Robot Chronicles

 This mini-game has several overlapping missions that correspond to different networkers on MLN:

- Lego City construction missions: [Foreman Frank](https://mylegonetwork.fandom.com/wiki/Foreman_Frank)
- Lego Agents missions: [Agent Chase](https://mylegonetwork.fandom.com/wiki/Agent_Chase)
- Lego Racers missions: [Peelie Wheelie](https://mylegonetwork.fandom.com/wiki/Peelie_Wheelie)

You can befriend each of these users without any requirements. Although the mini-game has 7 "levels", there are actually only 5 "awards" that it will send to MLN:

1. Crane Quest (City): No reward or message, but the button appears in-game
2. Speed Inferno Challenge (Racers): If you win, Peelie Wheelie will send you some Racing Trophies
3. Infestation (Agents): Completing this mission will have Agent Chase send you some Agent's Dossiers
4. Towing the line (City): Completing this mission will have Foreman Frank send you some Hard Hats
5. The Fall of the Robot Defeating this level will have Mayor Frictionfit send you the Keys to the City

## Lego City Coast Guards

This mini-game has just one associated networker: [Old Capt Joe](https://mylegonetwork.fandom.com/wiki/Old_Capt_Joe). When you beat the first level of the mini-game and he will send you the `Coast Guard Badge, Rank 1 Blueprint`. Once you have built the badge, you can befriend him. Playing through the rest of the game will grant the 4 other badges

## Lego City Construction

This mini-game has several levels that unlock vehicles and buildings of different categories. instead of getting awards per level, you get awards for finishing each category, called a "garage". The garages are as follows:

1. Construction
2. Fire
3. Police
4. Transit
5. Farm
6. Cargo
7. City

These garages correspond to in-game items that can be shown on the [Lego City Trophy Module](https://mylegonetwork.fandom.com/wiki/LEGO_CITY_Trophy_Module). When the user completes a garage, [Jack Drill](https://mylegonetwork.fandom.com/wiki/Jack_Drill) will send them the correct item.
