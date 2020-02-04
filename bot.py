import os, pymongo, pprint, datetime
import config
from datetime import datetime
from pymongo import MongoClient
from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient

# Instantiate Mongo Client
mongo_client = MongoClient("mongodb+srv://"
    + config.username + ":" + config.password
    + config.db_link)

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

admin_id = config.admin_id
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
      try:
        byte_count = collection.find_one({"name": team})
        if byte_count is not None:
          response = "%s currently has %d bytes!" % (team, byte_count["bytes"])
          slack_client.api_call("chat.postMessage", channel=channel_id, text=response)
        else:
          response = "%s does not compete for bytes." % team
          slack_client.api_call("chat.postMessage", channel=channel_id, text=response)
      except TypeError:
        response = "That team does not exist."
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
    if (collection.find_one({"_id": user_id})["birthday"] == "Update"):
      increaseBits(user_id, 1)

    datetime.strptime(date, '%m-%d')
    collection.find_one_and_update({'_id': user_id}, {'$set': {'birthday': date}})
    return "Birthday updated to %s!" % datetime.strptime(date, '%m-%d').strftime("%B %d")
  except ValueError:
    return "Incorrect date format, should be MM-DD"

def findAndRetrieveBday(user_id):
  db_data = collection.find_one({"_id": user_id})
  if db_data is None:
    createProfile(user_id)
    response_team = "Your birthday is not yet on our database. Use 'add bday MM-DD' to add yours to your profile!"
  else:
    bday = db_data["birthday"]
    if bday != "Update":
      bday = datetime.strptime(bday, '%m-%d').strftime("%B %d")
      response_team = 'Your birthday is on %s!' % bday
    else:
      response_team = "Your birthday is not yet on our database. Use 'add bday MM-DD' to add yours to your profile!"
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

def increaseBits(user_id, num_inc):
  collection.find_one_and_update({'_id': user_id}, {'$inc': {'bits': int(num_inc)}})
  return

def updateBits(user_id, numToSet):
  collection.find_one_and_update({'_id': user_id}, {'$set': {'bits': int(numToSet)}})
  return

# Respond to DMs
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  text = message.get('text')
  user_id = message["user"]
  channel_id = message["channel"]

  if message.get("subtype") is None and user_id != bogbot_id:
    if ("hi" in text[0:2] or "hello" in text[0:5]):
      response = 'Hello <@%s>! :tada:' % user_id
    elif "cheatsheet" in text[0:10]:
      response = config.cheatsheet_link
    elif "add bit" in text[0:7] and user_id == admin_id:
      try:
        userToAdd, num_inc = text.split(' ')[2], text.split(' ')[3]
        userToAdd = userToAdd[2:-1]
        increaseBits(userToAdd, num_inc)
        new_bit_count = collection.find_one({"_id": userToAdd})['bits']
        response = "%s Bits added for <@%s>, making their Bit count: %d" % (num_inc, userToAdd, new_bit_count)
      except NameError:
        response = "Missing a parameter"
    elif "set bit" in text[0:7] and user_id == admin_id:
      try:
        userToAdd, numToSet = text.split(' ')[2], text.split(' ')[3]
        userToAdd = userToAdd[2:-1]
        updateBits(userToAdd, numToSet)
        new_bit_count = collection.find_one({"_id": userToAdd})['bits']
        response = "<@%s> Bit count: %d" % (userToAdd, new_bit_count)
      except NameError:
        response = "Missing a parameter"
    elif "see bit" in text[0:7] and user_id == admin_id:
      try:
        userToAdd = text.split(' ')[2]
        userToAdd = userToAdd[2:-1]
        bit_count = collection.find_one({"_id": userToAdd})['bits']
        response = "<@%s> Bit count: %d" % (userToAdd, bit_count)
      except NameError:
        response = "Missing a parameter"
    elif "bit" in text[0:3]:
      bit_count = findAndRetrieveBits(user_id)
      response = 'Your Bit count: %d' % bit_count
    elif "add byte" in text[0:8] and user_id==admin_id:
      try:
        team, num_inc = text.split(' ')[2], text.split(' ')[3]
        updateTeamBytes(team, num_inc)
        response = "Bytes Added for Team %s!" % team
      except NameError:
        response = "Missing a parameter"
    elif "see byte" in text[0:8]:
      try:
        team = text.split(' ')[2]
        try:
          byte_count = collection.find_one({"name": team})['bytes']
          response = "Team %s byte count: %d" % (team, byte_count)
        except TypeError:
          if team in ["Marketing", "Community", "Product Ops", "Finance", "Events"]:
            response = "Committees do not compete for Bytes"
          elif team in ["Exec", "Bootcamp", "Website", "NPP"]:
            response = "%s does not compete for Bytes" % team
          else:
            response = "Invalid team name (use title-case) \n Options: BGC Safety, BGC Dynamics, DMS, Liv2BGirl, MedShare, Miqueas, Ombudsman, PACTS, VMS"
      except NameError:
        response = "Missing a parameter"
    elif "byte" in text[0:5]:
      response = ''
      findAndRetrieveBytes(channel_id, user_id)
    elif "team" in text[0:4]:
      team = findAndRetrieveTeam(user_id)
      response = '<@%s> is on team %s!' % (user_id, team)
    elif "add bday" in text[0:8]:
      birthday_date = text.split(' ')[2]
      response = add_birthday(user_id, birthday_date)
    elif "bday" in text[0:4]:
      response = findAndRetrieveBday(user_id)
    elif "help" in text[0:4]:
      response = "Try typing: cheatsheet, bit/bits, byte/bytes, team, or bday"
    elif "execute order 66" in text and user_id==admin_id:
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