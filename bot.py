import os, pymongo, pprint, datetime, schedule
import config
from datetime import datetime
from pymongo import MongoClient
from slackeventsapi import SlackEventAdapter
from slack import WebClient

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
slack_client = WebClient(slack_bot_token)

# Slack ID for admin and Bot
admin_id = config.admin_id
bogbot_id = slack_client.auth_test()["user_id"]

# Important channels
announce_channel = config.announcements_id
test_channel = config.test_id
bits_channel = config.bits_id
dogs_channel = config.dogs_id
memes_channel = config.meme_id
im_channel = config.im_id

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
          slack_client.chat_postMessage(channel=channel_id, text=response)
        else:
          response = "%s does not compete for bytes." % team
          slack_client.chat_postMessage(channel=channel_id, text=response)
      except TypeError:
        response = "That team does not exist."
        slack_client.chat_postMessage(channel=channel_id, text=response)
  return 'Ok'

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
  user_data = slack_client.users_info(user=user_id)['user']
  post = {"_id": user_id, "name": user_data['real_name'], "team": "Update", "bits": 0, "birthday": "Update"}
  collection.insert_one(post)
  return 'Oks'

def executeOrder66(channel_info):
  members = slack_client.conversations_members(channel=channel_info, limit=200)["members"]
  for member in members:
    db_data = collection.find_one({"_id": member})
    if db_data is None:
      createProfile(member)
  return 'Ok'

def updateTeamBytes(team_name, num_inc):
  collection.find_one_and_update({'name': team_name}, {'$inc': {'bytes': int(num_inc)}})
  return 'Ok'

def increaseBits(user_id, num_inc):
  collection.find_one_and_update({'_id': user_id}, {'$inc': {'bits': int(num_inc)}})
  return 'Ok'

def updateBits(user_id, numToSet):
  collection.find_one_and_update({'_id': user_id}, {'$set': {'bits': int(numToSet)}})
  return 'Ok'

def findTopFiveBits():
  result = collection.find()
  member_bits = []
  fakeVar = 0
  for user in list(result):
    try:
      if user['bits'] < 999:
        member_bits.append((user["_id"], user["bits"]))
    except KeyError:
      fakeVar += 1
  topBits = sorted(member_bits, key = lambda x: x[1], reverse=True)
  response = "Current Bit Standings:\n 1. <@%s> with %d bits!\n 2. <@%s> with %d bits!\n 3. <@%s> with %d bits!\n 4. <@%s> with %d bits!\n 5. <@%s> with %d bits!" % (topBits[0][0], topBits[0][1], topBits[1][0], topBits[1][1], topBits[2][0], topBits[2][1], topBits[3][0], topBits[3][1], topBits[4][0], topBits[4][1])
  return response

def findTopThreeBytes():
  result = collection.find()
  team_bytes = []
  fakeVar = 0
  for user in list(result):
    try:
      if user['bytes'] >= 0:
        team_bytes.append((user["name"], user["bytes"]))
    except KeyError:
      fakeVar += 1
  topBytes = sorted(team_bytes, key = lambda x: x[1], reverse=True)
  response = "Current Byte Standings:\n 1. Team %s with %d bytes!\n 2. Team %s with %d bytes!\n 3. Team %s with %d bytes!" % (topBytes[0][0], topBytes[0][1], topBytes[1][0], topBytes[1][1], topBytes[2][0], topBytes[2][1])
  return response

def displayRankings():
  response = findTopFiveBits()
  response = response + "\n\n" + findTopThreeBytes() + "\n\n Bit/Byte Cheatsheet:\n" + config.cheatsheet_link
  slack_client.chat_postMessage(channel=test_channel, text=response)
  return 'OK'

def postRankings():
  response = findTopFiveBits()
  response = response + "\n\n" + findTopThreeBytes() + "\n\n Bit/Byte Cheatsheet:\n" + config.cheatsheet_link
  slack_client.chat_postMessage(channel=announce_channel, text=response)
  return 'OK'

def parseNames(message):
  users = []
  users.append(message['user'])
  text = message.get('text')
  text = text.split(' ')
  for word in text:
    if len(word) > 3 and word[0] == '<' and word[-1] == '>':
      users.append(word[2:-1])
  return users

# def checkSameTeam(user_ids):
#   for user in user_ids:

# Respond to DMs
@slack_events_adapter.on("message")
def handle_message(event_data):
  message = event_data["event"]
  text = message.get('text')
  user_id = message["user"]
  channel_id = message["channel"]
  channel_type = message["channel_type"]
  timestamp_message = message["ts"]

  if channel_type == "channel":
    if user_id != bogbot_id and channel_id == test_channel:
      if text != '' and "files" in message:
        slack_client.reactions_add(channel=test_channel, name="doughnut", timestamp=timestamp_message)
        slack_client.reactions_add(channel=test_channel, name="camera_with_flash", timestamp=timestamp_message)
      else:
        slack_client.reactions_add(channel=test_channel, name="michelle_facepalm", timestamp=timestamp_message)
        slack_client.reactions_add(channel=test_channel, name="face_with_monocle", timestamp=timestamp_message)
      dateUsers = parseNames(message)
      for user in dateUsers:
        increaseBits(user, 0)
        new_bit_count = collection.find_one({"_id": user})['bits']
        response = "2 Bits added for <@%s>, making their Bit count: %d" % (user, new_bit_count)
        slack_client.chat_postMessage(channel=im_channel, text=response)

  else:
    if channel_type == "im" and message.get("subtype") is None and user_id != bogbot_id:
      if ("hi" in text[0:2] or "hello" in text[0:5]):
        response = 'Hello <@%s>! :tada:' % user_id
      elif "cheatsheet" in text[0:10]:
        response = config.cheatsheet_link
      elif "chanid" in text[0:6] and user_id == admin_id:
        response = "Channel id: " + channel_id
      elif "see rank" in text[0:8] and user_id == admin_id:
        displayRankings()
        response = "Displayed!"
      elif "post rank" in text[0:9] and user_id == admin_id:
        postRankings()
        response = "Displayed!"
      elif "see bitrank" in text[0:11] and user_id == admin_id:
        response = findTopFiveBits(channel_id)
      elif "see byterank" in text[0:12] and user_id == admin_id:
        response = findTopThreeBytes(channel_id)
      elif "add bit" in text[0:7] and user_id == admin_id:
        try:
          usersToAdd, num_inc = text.split(' ')[2:-1], text.split(' ')[-1]
          for user in usersToAdd:
            user = user[2:-1]
            increaseBits(user, num_inc)
            new_bit_count = collection.find_one({"_id": user})['bits']
            response = "%s Bits added for <@%s>, making their Bit count: %d" % (num_inc, user, new_bit_count)
            slack_client.chat_postMessage(channel=channel_id, text=response)
          response = ' '
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
          team = text.split(' ')[2]
          if team == "BGC":
            team = team + " " + text.split(' ')[3]
            num_inc = text.split(' ')[4]
          else:
            num_inc = text.split(' ')[3]
          updateTeamBytes(team, num_inc)
          new_byte_count = collection.find_one({"name": team})['bytes']
          response = "%s Bytes Added for Team %s, making their Byte count: %d!" % (num_inc, team, new_byte_count)
        except NameError:
          response = "Missing a parameter"
      elif "see byte" in text[0:8]:
        try:
          team = text.split(' ')[2]
          if team == "BGC":
            team = team + " " + text.split(' ')[3]
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
        except IndexError:
          response = "Missing a parameter"
      elif "byte" in text[0:5]:
        response = ' '
        findAndRetrieveBytes(channel_id, user_id)
      elif "team" in text[0:4]:
        team = findAndRetrieveTeam(user_id)
        response = '<@%s> is on team %s!' % (user_id, team)
      elif "add bday" in text[0:8]:
        try:
          birthday_date = text.split(' ')[2]
          response = add_birthday(user_id, birthday_date)
        except IndexError:
          response = "Missing 'date' parameter. Use 'add bday MM-DD' to add your birthday!"
      elif "bday" in text[0:4]:
        response = findAndRetrieveBday(user_id)
      elif "help" in text[0:4]:
        response = "Available commands:\n" \
          + "hi or hello                        Welcome message.\n" \
          + "cheatsheet                       Link to bits/bytes cheatsheet.\n" \
          + "team                                 See your current team(s).\n" \
          + "bits                                   See your current bit count.\n" \
          + "bytes                                See your current byte count.\n" \
          + "see bytes [team]             See the current byte count for a specific team\n" \
          + "bday                                 Display your birthday.\n" \
          + "add bday [MM-DD]        Adds your birthday to the database."
      elif "execute order 66" in text and user_id==admin_id:
        executeOrder66(channel_id)
        response = "Executed my Lord"
      else:
        response = "Unknown command. Type 'help' for list of commands."

      slack_client.chat_postMessage(channel=channel_id, text=response)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))

# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
slack_events_adapter.start(host="0.0.0.0", port=3000)

# Check BDay

# Update Bit/Byte Rankings Every Week
# schedule.every().wednesday.at("20:16").do(displayRankings)

# channel_list = slack_client.conversations_list(limit=500)["channels"]
# for channel in channel_list:
#   if channel["name"] == 'gt-bot-testing':
#     print(channel)