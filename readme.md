# launchbot
Discord bot using discord.py and python-launch-library.


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
Replace the XXXXXXXXX with your client ID and go to:
https://discordapp.com/oauth2/authorize?client_id=XXXXXXXXXXXX&scope=bot
You can find your client ID from the general information tab.
There you can add the bot to your server(s).

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
List of user IDs of people who can command the bot to shut down.
To get user ID, you must enable developer mode in discord. (Appearance settings)
Right click user, and click "Copy ID"
Example:
```
Authorities = 217611234569749337, 217611234569123377
```

##### Powerroles
List of rolenames that can command the bot to shut down.
Example:
```
Powerroles = Admin, Owner, Moderator
```

### Running the bot
You can run the bot by using command:
```
pipenv run main.py
```
Go to the server and test the bot1


Here is invite to my discord testserver.
https://discord.gg/zYpAFsw
Feel free to open issues and pull requests.
