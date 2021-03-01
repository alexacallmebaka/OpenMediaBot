# OpenMediaBot
OpenMediaBot is a Python library for creating media bots.

### What exactly is a media bot?
The name pretty much says it all. A media bot is a bot dedicated to supplying various media. This can include but is not limited to photo, audio, or video. One example of a media bot that runs off this library is [@SetsuPropaganda](https://twitter.com/SetsuPropaganda) on Twitter.


# Table of Contents
* [Requirements](#requirements)
* [Database Structure](#database-structure)
* [Media Objets](#media-objects)
* [Bots](#Bots)
    * [Twitter Bots](#twitter-bots)
* [Configuration Options](#configuration-options)
* [Google Drive](#google-drive)
* [Example](#example)

# Requirements
You will need to have Python 3.7 or higher installed on your system, as well as the following Python packages:

| Package                                            | Version Used*|
|----------------------------------------------------|--------------|
|__[pydrive2](https://pypi.org/project/PyDrive2/)__  |1.6.2         |
|__[twython](https://pypi.org/project/twython/)__    |3.8.2         |
|__[simplejson](https://pypi.org/project/twython/)__ |3.17.2        |
|__[pillow](https://pypi.org/project/twython/)__     |8.0.0         |

<sub>*\*These are just the versions of the packages I used. These versions are not required, but they have been confirmed compatible.*</sub>

# Database Structure
OpenMediaBot keeps track of all media in a SQLite3 Database. The schema is as follows:
```
ID text PRIMARY KEY
NAME text NOT NULL
LOCATION text NOT NULL
POSTED BOOLEAN NOT NULL
```
The ID is a unique identifier for the file. For local files, it is the file path. For Google Drive, it is the Google Drive file ID. Location denotes where the file is, for example, LOCAL or DRIVE would be valid values here.

# Media Objects
Media within OpenMediaBot is handled using a special object.
```
from OMB.bot import Media

media = Media(data, mimetype, name, id)
```
The "data" argument takes a file-like object. The "id" parameter is a unique identifier for the file. For a local file, this is the file path. For a Google Drive file, this is the Google Drive file ID.

# Bots
All bots inherit from the `Bot` baseclass. This class handles things such as database management, downloading photos from external sources, and setting configuration. It has several methods.

|Method|Description|Arguments|
|------|-----------|------|
|`updatedb()`|Update the database, or create it if it does not exist.|None|
|`resetdb()`|Sets the "posted" value of every database entry to False.|None|
|`DownloadFromDrive()`|Returns a media object constructed from a Google Drive File ID.|id|
|`GetRandom()`|Returns a media object created from a random database entry.|no_repeat=True|

In theory, OpenMediaBot can be designed to work with any platform. Currently, it is only designed to work with Twitter out of the box.

## Twitter Bots
Twitter bots are handled using the `TwitterBot` class, whcih is a subclass of `Bot`. The class can be instantiated as follows:
```
from OMB.twitter_bot import TwitterBot

bot = TwitterBot()
```
In order to post to Twitter, you must be authenticated using Oauth 1. OpenMediaBot requires these to be passed in a JSON file formatted as follows:
```
{"CONSUMER_KEY":<your API key>,
"CONSUMER_SECRET":<your API key secret>,
"ACCESS_TOKEN":<your Oauth token>,
"ACCESS_TOKEN_SECRET":<your Oauth token secret>}
```
These credentials can be obtained by registering for a [Twitter Developer Account](https://developer.twitter.com) and then creating a standalone app or project.

By default, OpenMediaBot looks for the credential file in `creds/twitter_creds.json`. If you would like to provide the file in a different location, pass it to the constructor as `twitter_credfile = "/path/to/credfile"`.

As of now, `TwitterBot` has one special method.
|Method|Description|Arguments|
|------|-----------|------|
|`post()`|Posts a piece of media to Twitter.|media="random", status=None, updatedb=True|

The agruments of `post()` deserve a little bit of extra explaination. `media` must be an [OMB media object](#media-objects). The default behavior is just to pick a random one from the database. `updatedb` refers to if the database is updated on each run. `status` is the text to be posted along with the media.

# Configuration Options
There are many options that can be passed to configure the bot. These can either be passed as keyword arguments, or passed in a JSON file using the `configfile=` in the bot constructor.
|Option|Description|Type|Default|
|------|-----------|----|-------|
|`name`|Name of the bot.|string| Bot|
|`db`|Location of the database.|string|media.db|
|`logpath`|Path to log file.|string|None|
|`drive_folders`|Drive Folder IDs.|array of strings|None|
|`local_folders`|Paths to local folders.|array of strings|None|
|`dm_errors`*|Send reports via Twitter DMs when the bot fails to post.|bool|True|
|`admin_ids`*|The Twitter IDs of the users to DM with error reports.| array of integers|None|

<sub>**These options are only available for a Twitter bot*</sub>

# Google Drive
OpenMediaBot uses PyDrive2 to interface with Google Drive. Instructions on how to obtain Google Oauth2 credentials can be found [here](https://pythonhosted.org/PyDrive/quickstart.html#authentication). OpenMediaBot utilizes a `settings.yaml` file in order automate Google Drive Authentication. Create a `settings.yaml` in the same directory the bot which contains the following:
```
client_config_backend: settings
client_config_file: <Path/to/oauth/creds/file/>
client_config:
  client_id: <your oauth client id>
  client_secret: <your oauth client secret>

save_credentials: True
save_credentials_backend: file
save_credentials_file: <path/to/jsonfile/in/which/to/save/creds>

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive
  - https://www.googleapis.com/auth/drive.scripts
```
More info on `settings.yaml` files can be found [here](https://pythonhosted.org/PyDrive/oauth.html#automatic-and-custom-authentication-with-settings-yaml).
# Example
The following is an example of an OpenMediaBot Twitter bot.

## Keyword Arguments Method
```
from OMB.twitter_bot import TwitterBot

bot = TwitterBot(admin_ids=[<Admin Twitter ID>],
drive_folders=[<Drive Folder ID>],
name="SetsunaPropaganda",
logpath="SETSUNA_BOT.log")

bot.post()
```

## Configuration File Method
```
from OMB.twitter_bot import TwitterBot

bot = TwitterBot(configfile="config.json")

bot.post()
```
The contents of `config.json`:
```
{"admin_ids": [<Admin Twitter ID>], 
"drive_folders":[<Drive Folder ID>],
"name":"SetsunaPropaganda",
"logpath":"SETSUNA_BOT.log"}
```
This is a pretty simple implementation of OpenMediaBot. A more complex example can be found [here](https://github.com/alexacallmebaka/MISATO_PICS_BOT).