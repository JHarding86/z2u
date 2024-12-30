import requests
import datetime
from datetime import time
import json
import argparse
import os
import xml.etree.ElementTree as ET
from epgTools import epgTools
from lxml import etree

input_file = "temp/downloaded_file.m3u"
allNHL_m3u = "temp/nhlall.m3u"
custom_m3u = "customNHL.m3u"
custom_epg = "customNHL.xml"

cleaned_file = 'temp/cleaned_epg_data.xml'
output_file = 'temp/nhl_epg_data.xml'

data = json
unique_ids = []
channelCount = 0
root = ET.Element('tv')

def getNHLSchedule(file_name):
    # Get the current date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # current_date = "2024-12-27"
    url = f"https://api-web.nhle.com/v1/schedule/{current_date}"

    # Send a GET request to the URL
    response = requests.get(url)

    # Save the content to a local file
    
    with open(file_name, 'wb') as file:
        file.write(response.content)

    print(f"File downloaded and saved as {file_name}")

def parseNHLScheduleToJSON(file_name):
    # Open and parse the JSON file
    with open(file_name, 'r', encoding='utf-8') as file:
        global data 
        data = json.load(file)

    print("JSON data has been parsed:")
    # print(json.dumps(data, indent=4))

def parse_m3u_file(file_name):
    channels = []
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            extinf_line = lines[i].strip()
            url_line = lines[i + 1].strip()
            if extinf_line.startswith("#EXTINF"):
                channel_info = {
                    "extinf": extinf_line,
                    "url": url_line
                }
                channels.append(channel_info)
    return channels

def createSingleChannelEPGData(UniqueID, tvgName, logo):
     #Creating M3U8 Data
    xmlChannel      = ET.Element('channel')
    xmlDisplayName  = ET.Element('display-name')
    xmlIcon         = ET.Element('icon')

    xmlChannel.set('id', UniqueID)
    xmlDisplayName.text = tvgName
    xmlIcon.set('src', logo)

    xmlChannel.append(xmlDisplayName)
    xmlChannel.append(xmlIcon)

    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName, description):
    #Creating EPG Data
    programme   = ET.Element('programme')
    title       = ET.Element('title')
    desc        = ET.Element('desc')
    category    = ET.Element('category')

    programme.set('start', startTime + " +0000")
    programme.set('stop', stopTime + " +0000")
    programme.set('channel', UniqueID)

    title.text = channelName

    desc.text = description

    category.set('lang', "en")
    category.text = "Sports"

    programme.append(title)
    programme.append(desc)
    programme.append(category)

    return programme

def outputM3ULine(teamName, otherTeam, link, logo, dateString, isThereAGame = 1):
    UniqueID = unique_ids.pop(0)
    global channelCount
    tvgName = "OpenChannel" + str(channelCount).zfill(3)
    tvLabel = tvgName
    channelCount += 1
    with open(custom_m3u, 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
        file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{logo}" group-title="James Custom", {tvLabel}\n')
        file.write(link + "\n")

    #Creating EPG Data
    xmlChannel = createSingleChannelEPGData(UniqueID, tvgName, logo)
    root.append(xmlChannel)

    #NHL schedule has times in UTC. Plex does a good job of converting these times for presentation in your time zone.
    #There is a problem when an entire channel is dedicated to a single show. That is at the begining of the day, you would
    #like the channel to show the date and time so you know when it comes on. UTC time must be used for this, so some trickery
    #must be used to come up with the correct start of day time.

    #To account for this, you must adjust the UTC time to your timezone (here it is adjusting for MST -7hrs):
        #Items Needed:
            #A start time for the day in UTC. - Midnight of that day in UTC, Used as fake filler data
            #An end time for the fake filler data
            #A start time for the actual game
            #An end time for the actual game.
            #Start and end time for filler data for the rest of the day

    utc_game_S_programme = datetime.datetime.strptime(dateString, '%Y-%m-%dT%H:%M:%SZ')
    utc_game_E_programme = utc_game_S_programme + datetime.timedelta(hours=2.5)

    mst_game_E_programme = utc_game_E_programme - datetime.timedelta(hours=7)
    game_end_of_day = datetime.datetime.combine(mst_game_E_programme, time.max) + datetime.timedelta(hours=7)

    game_mst = utc_game_S_programme - datetime.timedelta(hours=7)
    game_mst_day_start = datetime.datetime.combine(game_mst, time.min)
    start_first_fill = game_mst_day_start + datetime.timedelta(hours=7)
    end_first_fill = utc_game_S_programme - datetime.timedelta(seconds=1)

    start_second_fill = utc_game_E_programme + datetime.timedelta(seconds=1)
    end_second_fill = game_end_of_day
    mst_game_S_display = utc_game_S_programme - datetime.timedelta(hours=7)

    # print(f"Game Time: {utc_game_S_programme} {utc_game_E_programme}")
    # print(f"First Fill:  {start_first_fill} {end_first_fill}")
    # print(f"Game Fill:   {utc_game_S_programme} {utc_game_E_programme}")
    # print(f"Second Fill: {start_second_fill} {end_second_fill}")
    # print(f"Game Display Time: {mst_game_S_display}")

    channelNamePre  = f"Pre-Game {teamName} vs {otherTeam} - {mst_game_S_display.strftime('%m/%d/%Y %I:%M %p')}"
    channelName     = f"{teamName} vs {otherTeam} - {mst_game_S_display.strftime('%m/%d/%Y %I:%M %p')}"
    channelNamePost = f"Post-Game {teamName} vs {otherTeam} - {mst_game_S_display.strftime('%m/%d/%Y %I:%M %p')}"

    if isThereAGame:
        programme = createSingleEPGData(start_first_fill.strftime('%Y%m%d%H%M%S'), end_first_fill.strftime('%Y%m%d%H%M%S'), UniqueID, channelNamePre, "Fill Block for the day.")
        root.append(programme)
        programme = createSingleEPGData(utc_game_S_programme.strftime('%Y%m%d%H%M%S'), utc_game_E_programme.strftime('%Y%m%d%H%M%S'), UniqueID, channelName, "This is the game!")
        root.append(programme)
        programme = createSingleEPGData(start_second_fill.strftime('%Y%m%d%H%M%S'), end_second_fill.strftime('%Y%m%d%H%M%S'), UniqueID, channelNamePost, "This game has ended.")
        root.append(programme)
    else:
        programme = createSingleEPGData(start_first_fill.strftime('%Y%m%d%H%M%S'), end_second_fill.strftime('%Y%m%d%H%M%S'), UniqueID, "No Game", "There is no game on this channel for this day.")
        root.append(programme)

def createEPG(dateIndex):
    games = data["gameWeek"][dateIndex]["games"]
    # print(games)

    # Read the m3u file so we have a basis for the channel that a team is associated with
    nhlChannels = parse_m3u_file(allNHL_m3u)

    dateString = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")#2024-12-28T00:00:00Z
    for game in games:
        awayTeamName = game["awayTeam"]["commonName"]["default"]
        awayTeamLogo = game["awayTeam"]["logo"]
        homeTeamName = game["homeTeam"]["commonName"]["default"]
        homeTeamLogo = game["homeTeam"]["logo"]
        dateString = game["startTimeUTC"]

        gameName = f"{awayTeamName} at {homeTeamName}"

        print(f"{gameName} @ {dateString}")
        i = 0
        while i < len(nhlChannels):
            channel = nhlChannels[i]
            if awayTeamName.lower() in channel["extinf"].lower():
                # print(f"We found match for away team {awayTeamName} - {line}")
                outputM3ULine(awayTeamName, homeTeamName, channel["url"], awayTeamLogo, dateString)
                nhlChannels.pop(i)
                break
            # if homeTeamName.lower() in channel["extinf"].lower():
            #     # print(f"We found match for home team {homeTeamName} - {line}")
            #     outputM3ULine(homeTeamName, awayTeamName, channel["url"], homeTeamLogo, dateString)
            i += 1

    #Make sure there are always at 35 channels made
    while len(nhlChannels) > 0:
        outputM3ULine("", "", nhlChannels[0]["url"], "https://upload.wikimedia.org/wikipedia/commons/8/8d/No-Symbol.svg", dateString, 0)
        nhlChannels.pop(0)

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()

    if os.path.isfile(custom_m3u):
        os.remove(custom_m3u)
        
    print("Downloading M3U File...")
    epgTools.downloadM3UFile(args.username, args.password, input_file)

    epgTools.filterM3UByKeywords(["NHL"], ["Network", " : ", "REPLAY"], input_file, allNHL_m3u)

    # epgTools.filterEPGByKeywords(cleaned_file, output_file, "NHL", False)

    print("Getting NHL Scheulde...")
    getNHLSchedule("temp/nhlSchedule.json")

    print("Parsing NHL Scheulde...")
    parseNHLScheduleToJSON("temp/nhlSchedule.json")

    # Generate unique IDs so that we always have the same place to put different channels
    global unique_ids
    unique_ids = epgTools.generate_unique_ids(80, 42)

    createEPG(0)

    tree = ET.ElementTree(root)
    with open(custom_epg, 'wb') as afile:
        xmlString = etree.fromstring(ET.tostring(root, encoding='utf-8').decode('utf-8'))
        afile.write(etree.tostring(xmlString, pretty_print=True, encoding='utf-8'))
    # tree.write(custom_epg, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    main()