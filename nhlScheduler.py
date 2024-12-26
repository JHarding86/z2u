import requests
import datetime
import json
import argparse
import random
import uuid
import os
import xml.etree.ElementTree as ET

input_file = "downloaded_file.m3u"
allNHL_m3u = "nhlall.m3u"
custom_m3u = "customNHL.m3u"
custom_epg = "customNHL.epg"

data = json
unique_ids = []
channelCount = 0
root = ET.Element('tv')

def getNHLSchedule(file_name):
    # Get the current date
    # current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_date = "2024-12-27"
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

def downloadM3UFile(user, password):
    url = f"https://line.empire-4k.cc/get.php?username={user}&password={password}&type=m3u&output=mpegts"

    # Send a GET request to the URL
    response = requests.get(url)

    # Save the content to a local file
    with open(input_file, 'wb') as file:
        file.write(response.content)

    print(f"File downloaded and saved as {input_file}")

def narrowDownChannels():
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, open(allNHL_m3u, 'w', encoding='utf-8') as outfile:
        lines = infile.readlines()
        i = 1
        while i < len(lines):
            line = lines[i].lower()
            # Check to make sure these item do not exist in the string
            # Check for "#EXTINF:-1,US" and keywords, Special exemption for adding a colorado avalanche specific channel
            if "#extinf:-1,nhl" in line and " : " in line:
                outfile.write(lines[i])  # Write the original line
                if i + 1 < len(lines):
                    outfile.write(lines[i + 1])
            i += 2

    print("Processing complete. Check the output file for results.")

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

def generate_unique_ids(count, seed=42):
    random.seed(seed)
    ids = []
    for _ in range(count):
        id_str = str(uuid.UUID(int=random.getrandbits(128)))  # Generate a unique UUID
        ids.append(id_str)
    global unique_ids
    unique_ids = ids

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

    programme.set('start', startTime + " +0000")
    programme.set('stop', stopTime + " +0000")
    programme.set('channel', UniqueID)

    title.text = channelName

    desc.text = description

    programme.append(title)
    programme.append(desc)

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

    start_date = datetime.datetime.strptime(dateString, '%Y-%m-%dT%H:%M:%SZ')

    global mStartTime
    mStartTime = start_date.strftime("%Y%m%d000000")
    stop_date = start_date + datetime.timedelta(days=2)
    global mStopTime
    mStopTime = stop_date.strftime("%Y%m%d000000")


    format_12_hour = start_date.strftime("%m/%d/%y")
    start_date = start_date - datetime.timedelta(hours=7)

    startHour = start_date.strftime("%I:%M %p") + " (MST)"
    format_12_hour = format_12_hour + " - " + startHour

    channelName = teamName + " vs " + otherTeam + " " + format_12_hour

    if isThereAGame:
        programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, channelName, "No Description.")
    else:
        programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, "No Game", "There is no game on this channel for this day.")
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
            if homeTeamName.lower() in channel["extinf"].lower():
                # print(f"We found match for home team {homeTeamName} - {line}")
                outputM3ULine(homeTeamName, awayTeamName, channel["url"], homeTeamLogo, dateString)
            i += 1

    #Make sure there are always at 35 channels made
    if channelCount < 35:
        for i in range(0, 35 - channelCount):
            outputM3ULine("", "", "http://line.empire-4k.cc:80/A32382/182D35/745248", "https://upload.wikimedia.org/wikipedia/commons/8/8d/No-Symbol.svg", dateString, 0)

        

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()

    if os.path.isfile(custom_m3u):
        os.remove(custom_m3u)
        
    print("Download M3U File...")
    downloadM3UFile(args.username, args.password)

    print("Narrowing down the channels to NHL channels...")
    narrowDownChannels()

    print("Getting NHL Scheulde...")
    getNHLSchedule("nhlSchedule.json")

    print("Parsing NHL Scheulde...")
    parseNHLScheduleToJSON("nhlSchedule.json")

    # Generate unique IDs so that we always have the same place to put different channels
    generate_unique_ids(80)

    createEPG(0)
    # createEPG(1)

    tree = ET.ElementTree(root)
    tree.write(custom_epg, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    main()