# amas_presence
A collection of utilites, script, bots, etc. for the SMITE Amateur League Discord Server Amaterasu's Presence

## Installation Instructions
Install Python 3.10+ (3.10, 3.11, etc)
Install (Poetry)[https://python-poetry.org/docs/#installation]

Download the Git Repo, navigate to the directory, and run the following:
```
poetry install
```

## Auth Instructions
Follow the steps (here)[] to retrieve a service account token `.json` file. Name it `gspread_auth_token.json` and place it one directory above the directory containing these files. In other words, place it in the directory which contains the directory containing these files. Also acquire the bot token from Momo, and place it in the same location.
```
stuff.txt
gspread_auth_token.json
amas_presence_helper_bot_token.txt
amas_presence
    discord_bot.py
    pyproject.toml
    etc...
```

## Run Instructions
Navigate to the root folder of this directory and run the following command:
```
poetry run python discord_bot.py
```

### Run Notes
You may see "heartbeat" errors when the `matchmake` command is running. As long as the bot doesn't fail to respond in the server, don't worry about it.
