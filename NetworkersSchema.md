Networkers can be imported using the `import_networkers_xml` command. However, XML files with networkers are not provided with the content files. The command accepts custom XML files that follow the schema described below.

# Schema
- Networkers are imported as long as they are a list of `<networker>` in the root tag `<networkers>`.
- Each `<networker>` can have the following attributes:
  - `name` (required) - Name of the networker.
  - `avatar` (required) - String representation of the avatar of the network. For PNGs stored in the content files, use `png`.
  - `rank` (required) - Rank of the networker.
  - `hidden` can be included for hidden networkers, but is not used currently.
- Each `networker` can have the following optional children:
  - `<page>` - Describes the theming of the page. There are 3 optional attributes:
    - `backgroundColor` - Color of the background if there is no skin. Must be a valid color id (1-9, 16-25, 32-40). 1 is default.
    - `columnColor` - Color of the columns if there is no skin. Must be a valid color id (1-9, 16-25, 32-40). 1 is default.
    - `skin` - Skin for the page that overrides background and color columns. Must be a valid item id. No value is used if not provided.
  - `<friendship>` - Specifies how the networker handles friendship requests.
    - Can have the following attributes:
      - `acceptMessageId` (required) - Message body id when the friendship is accepted.
      - `declineMessageId` (required if the child `<requiredItem>` exists) - Message body id when the friendship is declined.
    - Can have the optional child `<requiredItem id="ID"/>` where ID is the item id of an item the user must have to accept the friendship.
  - `<friends>` - List of `<networker name="NAME"/>` where NAME is the `name` of the networker to be friends with. Friends are bidirectional, but should be defined in both networkers since they are only created when the friended networker is already imported.
  - `<modules>` - List of `<module>`, which each containing the following parameters:
    - `type` (required if `id` is not present) - Type of the module (`Banner`, `Text`, `Sticker`, `Loop`, or `Trade`). It will specify the module if `id` is not present and handle other database entries for the module.
    - `id` (required if `type` is not present) - Id of the module to use. It will override the version based on the `type` (if present).
    - `x` (required) - X coordinate (column) of the module. Must be 0, 1, or 2.
    - `y` (required) - Y coordinate (Row) of the module. Must be 0, 1, 2, or 3.
    - `color` (optional) - Color id of the module. Must be a valid color id (1-9, 16-25, 32-40).
    - `bannerId` (required if `type` is `Banner`) - Id of the banner to display.
    - `text` (required if `type` is `Text`) - Text to display in the box.
    - `giveId` (required if `type` is `Sticker`, `Loop`, or `Trade`) - Id of the item the module gives to the user.
    - `giveQuantity` (optional) - Quantity of the item the module gives to the user. Only relevant for the `type` being `Trade`. Defaults to 1.
    - `requestId` (required if `type` is `Sticker`, `Loop`, or `Trade`) - Id of the item the module takes from the user.
    - `requestQuantity` (optional) - Quantity of the item the module tales from the user. Only relevant for the `type` being `Sticker`, `Loop`, or `Trade`. Defaults to 1.
  - `<messageTriggers>` - List of 2 potential children:
    - `<item>` - Triggers a response from the networker when an item is sent, regardless of message body. Must contain the attributes `id` for the id of the item and `responseId` for the id of the response body to send.
    - `<message>` - Triggers a response from the networker when a message body is sent. Must contain the attribute `responseId` for the id of the response body to send. To specify the required message body from the user, either the message body id must be given as the attribute `id`, or a helper `type` attribute to reference the message body (must be `HelpRequest`, `StickerRequest`, `LoopRequest`, or `TradeRequest`).
    - For both `<item>` and `<message>`, an `<attachment>` child can be added to specify an attachment. The attribute `id` is required for the id of the item to send, with an optional attribute `quantity` for how many to send (defaults to 1).
  - `<itemTriggers>` is unused but is planned for handling when a user obtains an item. List of 2 potential children:
    - `<firstTime>` - Triggers the networker to send a message when the user receives an item with the id from the attribute `itemId` for the first time. The attribute `messageId` is required for the message body id to send.
    - `<repeat>` - Triggers the networker to send a message when the user receives an item with the id from the attribute `itemId` after first time. The attribute `messageId` is required for the message body id to send.
    - For both `<firstTime>` and `<repeat>`, an `<attachment>` child can be added to specify an attachment. The attribute `id` is required for the id of the item to send, with an optional attribute `quantity` for how many to send (defaults to 1).

# Examples
```xml
<networkers>
    <!--png specifies a png image (NOT the path). Normal networkers can use normal avatar string representations.-->
    <networker name="MyNetworker" avatar="png" rank="2" hidden="false">
        <!--Optional page tag that makes the background color 20 and the column color 2.-->
        <page backgroundColor="20" columnColor="2"/>
        <!--Optional page tag that makes the background color 20 and the column color 1 (default).-->
        <page backgroundColor="20"/>
        <!--Optional page tag that makes the skin 1. Background color and column color are irrelevant.-->
        <page skin="20"/>
        
        <!--Makes the networker always accept friend requests and respond with the message id 1000.-->
        <friendship acceptMessageId="1000"/>
        <!--Makes the networker accept friend requests and respond with the message id 1000 if they have item id 2000. Otherwise, the requested is declined and the message id 1001 is sent back.-->
        <friendship acceptMessageId="1000" declineMessageId="1001">
            <requiredItem id="2000"/>
        </friendship>
        
        <!--List of modules to add.-->
        <modules>
            <!--Adds a banner at position 0,0 with the id 3000.-->
            <module type="Banner" x="0" y="0" bannerId="3000"/>
            <!--Adds a trade at position 0,1, offering 1 of item 2000 for 2 of item 2001.-->
            <module type="Trade" x="0" y="1" giveId="2000" giveQuantity="1" requestId="2001" requestQuantity="2"/>
            <!--Adds a trade (overriden with module id 2002) at position 0,2, offering 1 of item 2000 for 2 of item 2001, with color 20.-->
            <module type="Trade" id="2002" x="0" y="1" color="20" giveId="2000" giveQuantity="1" requestId="2001" requestQuantity="2"/>
            <!--Adds a text module at position 2,1.-->
            <module type="Text" x="2" y="1" text="My text."/>
            <!--Adds a sticker module at 2,2, requesting 2 of item 2001 for sticker 2003-->
            <module type="Sticker" x="2" y="2" color="20" giveId="2003" requestId="2001" requestQuantity="2"/>
            <!--Adds a loop module at 2,2, requesting 2 of item 2001 for loop 2004-->
            <module type="Loop" x="2" y="2" color="20" giveId="2004" requestId="2001" requestQuantity="2"/>
            <!--Adds an arbitrary module at position 0,3 with the id 3001.-->
            <module id="3001" x="0" y="3"/>
        </modules>
        
        <!--List of message triggers.-->
        <messageTriggers>
            <!--Networker sends message 1002 when item 2001 is sent.-->
            <item id="2001" responseId="1002"/>
            <!--Networker sends message 1003 and 3 of item 2002 when item 2001 is sent.-->
            <item id="2001" responseId="1002">
                <attachment id="2002" quantity="3"/>
            </item>
            <!--Networker sends message 1002 when message 1003 sent.-->
            <message id="1003" responseId="1002"/>
            <!--Networker sends message 1002 and 3 of item 2002 when message 1003 is sent.-->
            <message id="1003" responseId="1002">
                <attachment id="2002" quantity="3"/>
            </item>
            <!--Networker sends message 1002 when sent a help request. <attachment> can be added as well, like above.-->
            <message type="HelpRequest" responseId="1002"/>
            <!--Networker sends message 1002 when sent a sticker request. <attachment> can be added as well, like above.-->
            <message type="StickerRequest" responseId="1002"/>
            <!--Networker sends message 1002 when sent a loop request. <attachment> can be added as well, like above.-->
            <message type="LoopRequest" responseId="1002"/>
            <!--Networker sends message 1002 when sent a trade request. <attachment> can be added as well, like above.-->
            <message type="HelpRequest" responseId="1002"/>
        </messageTriggers>
        
        <!--List of item triggers (currently unimplemented).-->
        <itemTriggers>
            <!--Networker sends message 1002 when the user gets item 2001 the first time.-->
            <firstTime itemId="2001" messageId="1002"/>
            <!--Networker sends message 1002 and 3 of item 2002 when the user gets item 2001 the first time.-->
            <firstTime itemId="2001" messageId="1002">
                <attachment id="2002" quantity="3"/>
            </firstTime>
            <!--Networker sends message 1002 when the user gets item 2001 after the first time.-->
            <repeat itemId="1003" messageId="1002"/>
            <!--Networker sends message 1002 and 3 of item 2002 when the user gets item 2001 after the first time.-->
            <repeat itemId="1003" messageId="1002">
                <attachment id="2002" quantity="3"/>
            </repeat>
        </itemTriggers>
    </networker>
</networkers>
```