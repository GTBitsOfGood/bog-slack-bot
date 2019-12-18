import os, re, time
import datetime, pymongo
import config
from datetime import datetime
from pymongo import MongoClient
from slackclient import SlackClient

# Instantiate Mongo Client
mongo_client = MongoClient("mongodb+srv://"
    + config.username + ":" + config.password
    + "@bogbdaydb-j8wgl.mongodb.net/test?retryWrites=true&w=majority")

# Instantiate Slack Client
slack_client = SlackClient(config.token)

# Bot's User ID in Slack: Value is assigned after the Bot starts up
bogbot_id = None

# Specify DB
db = mongo_client["birthday"]
collection = db["spring2020"]

# Constants
RTM_READ_DELAY = 1 # Delay between reading from RTM
HELP_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

# Determines if commands are directed towards the Bot
def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a command is found, then the function returns a tuple of command and channel.
        If not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bogbot_id:
                return message, event["channel"]
    return None, None

# Figure out if the message starts with a mention, then compares the ID with that of the Bot
#
# If this ID is the same, then we know it is a Bot command, so we return the command text
# with the channel ID
def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text,
        then returns the user ID which was mentioned. If there is no direct mention,
        return None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # The first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

# If the command starts with a known command, it has an appropriate response
def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(HELP_COMMAND)

    # Finds and executes the given command, filling in response
    response = None

    # More commands
    if command.startswith(HELP_COMMAND):
        response = "Available commands:\n" \
        + "bday            Display birthdays today.\n" \
        + "myday         Display days until YOUR birthday.\n" \
        + "add              Adds a birthday to my database."

    elif command.startswith("bday"):
        response = "These are the birthdays today:"

    elif command.startswith("myday"):
        daysLeft = days_until_bday(command)
        response = "Days until your birthday: *" + str(daysLeft) + "*"

    elif command.startswith("add"):
        response = add_birthday(command)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel = channel,
        text = response or default_response
    )

def days_until_bday(command):
    return command

def add_birthday(command):
    toAdd = command.split(' ', 1)[1]
    user_id, message = parse_direct_mention(toAdd)
    try:
        datetime.strptime(message, '%m-%d')
        post = {"_id": user_id, "bday": message}
        collection.insert_one(post)
        return "Birthday added!"
    except ValueError:
        return "Incorrect date format, should be MM-DD"

if __name__ == "__main__":
    # Connect to Slack RTM API
    if slack_client.rtm_connect(with_team_state=False):
        print("BoG Bot connected and running!")
        # Read the Bot's User ID by calling Web API Method
        bogbot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")