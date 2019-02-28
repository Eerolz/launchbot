# launchbot
A discord bot that can alert about happening launches, and can be asked information about them as well as past ones.

This uses discord.py and python-launch-library.


## Setup
This project uses pipenv.

If you don't have pipenv installed, install it by using:
```
pip install pipenv
```

### Installing packages

To install required libraries run:
```
pipenv install
```

### Setupping the bot

#### Creating discord bot
Go to [discord developer portal](https://discordapp.com/developers/applications/) and create an application.
Go to the bot tab, and click "Add bot".
Go to OAuth2 tab and check the bot checkbox.
Go to the url that appears below, and add it to a server.

#### Configuring the bot.
Copy exampleconfig.ini as config.ini and modify it for your needs.

##### Prefix
The prefix the bot uses for commands.
For example:
```
Prefix = '!'
```
If you want to use mentioning the bot as prefix, you can do it like this:
```
Prefix = '<@1234567890> '
```
You need to copy the bot's client ID as the number.

##### Token
Copy the token from bot tab of the developer portal.
Example:
```
Token = NTwAsdk3OTIxNjasDfU51235.Dv7GsA.fmAI2nvEJWqWeEtygDyW4456EMQ
```
The token allows people to take over your bot, so don't give it to anyone.

##### Authorities
List of user IDs of people who can command the bot to shut down etc.
To get user ID, you must enable developer mode in discord. (Appearance settings)
Right click user, and click "Copy ID"
Example:
```
Authorities = 217611234569749337, 217611234569123377
```
Having your user ID is extremely helpful when restarting the bot.

##### Can_notify
Can the bot notify launch notify channel
```
Cannotify = yes
```
For notification to work, you need 'Launch notify' named role.

##### Keep_message
Will the bot keep the message it has sent or delete it after while
```
Keep_message = yes
```

##### Testchannel
Where the bot sends message when online.
Getting channel ID works similarly as getting user ID.
```
Testchannel = 432822312346572858
```
You can leave this empty.

##### Channels
List of channels that the bot will send launchalerts on.
```
Channels = 432822312346572858, 432823212372491258
```
You can leave this empty if you don't want launchalerts. This will change soon.

### Running the bot
You can run the bot by using command:
```
pipenv run main.py
```
If it doesn't work, try:
```
python3 pipenv shell
python3 main.py
```
Go to the server and test the bot!
Show all commands by using prefix + help.
Example:
```
!help
```
Currently it doesn't update information after launch for some reason. Use `!restart` after every launch to make sure all information is correct. :( Hopefully will find a solution for this problem.

You can ask questions or suggest commands on my [testserver](https://discord.gg/q5Xhk4S).
Or feel free to open issues and pull requests.
