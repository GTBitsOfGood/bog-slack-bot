import os, pymongo, pprint, datetime
import config
from datetime import datetime
from pymongo import MongoClient
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient

# Instantiate Mongo Client
mongo_client = MongoClient("mongodb+srv://"
    + config.username + ":" + config.password
    + "@spring2020-wjlnz.mongodb.net/test?retryWrites=true&w=majority")

# Specify DB
db = mongo_client["Spring2020"]
collection = db["member-manager"]
posts = db.posts

# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = config.signing_secret
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = config.slack_token
slack_client = SlackClient(slack_bot_token)

bogbot_id = slack_client.api_call("auth.test")["user_id"]

def findAndRetrieveBits(user_id):
  db_data = collection.find_one({"_id": user_id})
  if db_data is None:
    createProfile(user_id)
    bit_count = 0
  else:
    bit_count = db_data["bits"]
  return bit_count

def findAndRetrieveBytes(channel_id, user_id):
  db_data = collection.find_one({"_id": user_id})
  if db_data is None:
    createProfile(user_id)
  else:
    teams = db_data["team"].split(";")
    for team in teams:
      byte_count = collection.find_one({"name": team})
      if byte_count is not None:
        response = "%s currently has %d bytes!" % (team, byte_count["bytes"])
        slack_client.api_call("chat.postMessage", channel=channel_id, text=response)
      else:
        response = "%s does not compete for bytes." % team
        slack_client.api_call("chat.postMessage", channel=channel_id, text=response)
  return

def findAndRetrieveTeam(user_id):
  db_data = collection.find_one({"_id": user_id})
  if db_data is None:
    team = "Needs Updating"
    createProfile(user_id)
  else:
    team = db_data["team"]
    team = ", ".join(team.split(";"))
  return team

def add_birthday(user_id, date):
  try:
    datetime.strptime(date, '%m-%d')
    collection.find_one_and_update({'_id': user_id}, {'$set': {'birthday': date}})
    return "Birthday added!"
  except ValueError:
    return "Incorrect date format, should be MM-DD"

def findAndRetrieveBday(user_id):
  db_data = collection.find_one({"_id": user_id})
  if db_data is None:
    createProfile(user_id)
    response_team = 'Your birthday is not yet on our database.' % user_id
  else:
    bday = db_data["birthday"]
    if bday != "Update":
      bday = datetime.strptime(bday, '%m-%d').strftime("%B %d")
      response_team = 'Your birthday is on %s!' % bday
    else:
      response_team = 'Your birthday is not yet on our database. Use "addbday MM-DD" to add yours to your profile!' % user_id
  return response_team

def createProfile(user_id):
  user_data = slack_client.api_call("users.info", user=user_id)['user']
  post = {"_id": user_id, "name": user_data['real_name'], "team": "Update", "bits": 0, "birthday": "Update"}
  collection.insert_one(post)

def executeOrder66(channel_info):
  members = slack_client.api_call("conversations.members", channel=channel_info, limit=200)["members"]
  for member in members:
    db_data = collection.find_one({"_id": member})
    if db_data is None:
      createProfile(member)
  return

def updateTeamBytes(team_name, num_inc):
  collection.find_one_and_update({'name': team_name}, {'$inc': {'bytes': int(num_inc)}})
  return

# Respond to DMs
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  user_id = message["user"]
  channel_id = message["channel"]

  if message.get("subtype") is None and user_id != bogbot_id:
    if ("hi" in message.get('text') or "hello" in message.get('text')):
      response = 'Hello <@%s>! :tada:' % user_id
    elif ("bit" in message.get('text') or "bits" in message.get('text')):
      bit_count = findAndRetrieveBits(user_id)
      response = 'Bits for <@%s>: %d' % (user_id, bit_count)
    elif "addbytes" in message.get('text') and user_id=="UMXA2A2SZ":
      team, num_inc = message.get('text').split(' ')[1], message.get('text').split(' ')[2]
      updateTeamBytes(team, num_inc)
      response = "Bytes Added!"
    elif ("byte" in message.get('text') or "bytes" in message.get('text')):
      response = 'Keep collecting Bytes before the Binary Bash!'
      findAndRetrieveBytes(channel_id, user_id)
    elif "team" in message.get('text'):
      team = findAndRetrieveTeam(user_id)
      response = '<@%s> is on team %s!' % (user_id, team)
    elif "addbday" in message.get('text'):
      birthday_date = message.get('text').split(' ')[1]
      response = add_birthday(user_id, birthday_date)
    elif "bday" in message.get('text'):
      response = findAndRetrieveBday(user_id)
    elif "help" in message.get('text'):
      response = "Try typing: hi/hello, bit/bits, byte/bytes, team, or bday"
    elif "execute order 66" in message.get('text') and user_id=="UMXA2A2SZ":
      executeOrder66(channel_id)
      response = "Executed my Lord"
    else:
      response = "Unknown command. Type 'help' for list of commands."

    slack_client.api_call("chat.postMessage", channel=channel_id, text=response)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))

# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
slack_events_adapter.start(port=3000)