import sys
from lxml import etree
import requests
import random
import uuid
import os
import xml.etree.ElementTree as ET
import datetime
from datetime import time

class epgTools:
    sChannelCount = 0

    @staticmethod
    def filterEPGByKeywords(input_file, output_file, keyword, needsChannelID):
        try:
            with open(input_file, 'rb') as file:
                content = file.read()
                tree = etree.fromstring(content)

                # Find all channel elements
                channels = tree.findall('.//channel')
                # Find all programme elements
                programmes = tree.findall('.//programme')

                # Filter channels with keyword in display-name and non-blank ID
                channel_ids = []
                display_names = []
                # channel.get('id')
                # for channel in channels :
                #     if channel.get('id') and keyword in channel.find('display-name').text:
                        
                
                # Remove channels not in the US list
                for channel in channels:
                    add = False
                    channelID = channel.get('id')
                    dname = channel.find('display-name').text
                    if(needsChannelID):
                        if channelID != '' and keyword in channel.find('display-name').text:
                            add = True
                    else:
                        if keyword in dname:
                            print(dname + " " + channelID)
                            add = True
                    
                    if add == True:
                        channel_ids.append(channelID)
                        display_names.append(dname)

                # Remove channels not in the channel_ids list
                for channel in channels:
                    if channel.find('display-name').text not in display_names:
                        channel.getparent().remove(channel)

                # Remove programmes not linked to US channels
                for programme in programmes:
                    if programme.get('channel') not in channel_ids:
                        programme.getparent().remove(programme)

                # Write the filtered XML to a new file
                with open(output_file, 'wb') as output:
                    output.write(etree.tostring(tree, pretty_print=True, encoding='utf-8'))

                print(f"Filtered channels saved to '{output_file}'.")
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    @staticmethod
    def downloadM3UFile(user, password, outputFile):
        url = f"https://line.empire-4k.cc/get.php?username={user}&password={password}&type=m3u&output=mpegts"

        # Send a GET request to the URL
        response = requests.get(url, stream=True)

        # Get the total size of the response (in bytes)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        # Save the content to a local file
        with open(outputFile, 'wb') as file:
            # Iterate over the response content in chunks
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    percent = downloaded/total_size *100
                    print(f"\rProgress: {percent:.2f}%", end='', flush=True)

        print(f"File downloaded and saved as {outputFile}")
    
    @staticmethod
    def filterM3UByKeywords(includeKeywords, excludeKeywords, m3uInputFile, m3uOutputFile):
        with open(m3uInputFile, 'r', encoding='utf-8', errors='ignore') as infile, open(m3uOutputFile, 'w', encoding='utf-8') as outfile:
            lines = infile.readlines()
            i = 1
            while i < len(lines):
                line = lines[i].lower()
                # Check to make sure these item do not exist in the string
                # Check for "#EXTINF:-1,US" and keywords, Special exemption for adding a colorado avalanche specific channel
                if any(word.lower() in line for word in includeKeywords):
                    if all(word.lower() not in line for word in excludeKeywords):
                        outfile.write(lines[i])  # Write the original line
                        if i + 1 < len(lines):
                            outfile.write(lines[i + 1])
                i += 2

        print("Processing complete. Check the output file for results.")
    
    @staticmethod
    def parseM3UIntoObj(file_name):
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
    @staticmethod
    def generate_unique_ids(count, seed):
        random.seed(seed)
        ids = []
        for _ in range(count):
            id_str = str(uuid.UUID(int=random.getrandbits(128)))  # Generate a unique UUID
            ids.append(id_str)
        global unique_ids
        return ids
    
    @staticmethod
    def getChannelName(preName: str):
        channelName = preName + str(epgTools.sChannelCount).zfill(3)
        epgTools.sChannelCount += 1
        return channelName
    
    @staticmethod
    def createDirectory(dir):
        # Check if the directory already exists
        if not os.path.exists(dir):
            os.makedirs(dir)
            print(f"Directory '{dir}' created successfully.")
        else:
            print(f"Directory '{dir}' already exists.")

    @staticmethod
    def removeFile(fileName: str):
        if os.path.isfile(fileName):
            os.remove(fileName)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def outputM3ULine(root: ET.Element, teamName, otherTeam, link, logo, dateString, UniqueID, isThereAGame, channelName, m3uFile):
        tvgName = channelName
        tvLabel = tvgName
        with open(m3uFile, 'a', encoding='utf-8') as file:  # Use 'a' mode for appending
            file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{logo}" group-title="James Custom", {tvLabel}\n')
            file.write(link + "\n")

        #Creating EPG Data
        xmlChannel = epgTools.createSingleChannelEPGData(UniqueID, tvgName, logo)
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
        try:
            utc_game_S_programme = datetime.datetime.strptime(dateString, '%Y-%m-%dT%H:%M:%SZ')
        except:
            utc_game_S_programme = datetime.datetime.strptime(dateString, '%Y-%m-%dT%H:%MZ')

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
            programme = epgTools.createSingleEPGData(start_first_fill.strftime('%Y%m%d%H%M%S'), end_first_fill.strftime('%Y%m%d%H%M%S'), UniqueID, channelNamePre, "Fill Block for the day.")
            root.append(programme)
            programme = epgTools.createSingleEPGData(utc_game_S_programme.strftime('%Y%m%d%H%M%S'), utc_game_E_programme.strftime('%Y%m%d%H%M%S'), UniqueID, channelName, "This is the game!")
            root.append(programme)
            programme = epgTools.createSingleEPGData(start_second_fill.strftime('%Y%m%d%H%M%S'), end_second_fill.strftime('%Y%m%d%H%M%S'), UniqueID, channelNamePost, "This game has ended.")
            root.append(programme)
        else:
            programme = epgTools.createSingleEPGData(start_first_fill.strftime('%Y%m%d%H%M%S'), end_second_fill.strftime('%Y%m%d%H%M%S'), UniqueID, "No Game", "There is no game on this channel for this day.")
            root.append(programme)

    @staticmethod
    def createEPG(games, uniqueIDs, m3uInputFile, filePrefix):

        m3uFile = "custom" + filePrefix + ".m3u"
        epgFile = "custom" + filePrefix + ".xml"

        epgTools.removeFile(m3uFile)
        epgTools.removeFile(epgFile)

        root = ET.Element('tv')
        # Read the m3u file so we have a basis for the channel that a team is associated with
        channels = epgTools.parseM3UIntoObj(m3uInputFile)

        dateString = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")#2024-12-28T00:00:00Z
        for game in games:
            awayTeamName = game["away"]
            homeTeamName = game["home"]
            dateString = game["date"]
            logo = game["logo"]

            gameName = f"{awayTeamName} at {homeTeamName}"

            print(f"{gameName} @ {dateString}")
            i = 0
            while i < len(channels):
                channel = channels[i]
                if awayTeamName.lower() in channel["extinf"].lower():
                    # print(f"We found match for away team {awayTeamName} - {line}")
                    epgTools.outputM3ULine(root, awayTeamName, homeTeamName, channel["url"], logo, dateString, uniqueIDs.pop(0), True, epgTools.getChannelName(filePrefix), m3uFile)
                    channels.pop(i)
                    break
                # if homeTeamName.lower() in channel["extinf"].lower():
                #     # print(f"We found match for home team {homeTeamName} - {line}")
                #     outputM3ULine(homeTeamName, awayTeamName, channel["url"], homeTeamLogo, dateString)
                i += 1

        #Make sure there are always at 35 channels made
        while len(channels) > 0:
            epgTools.outputM3ULine(root, "", "", channels[0]["url"], "https://upload.wikimedia.org/wikipedia/commons/8/8d/No-Symbol.svg", dateString, uniqueIDs.pop(0), False, epgTools.getChannelName(filePrefix), m3uFile)
            channels.pop(0)
        
        with open(epgFile, 'wb') as afile:
            xmlString = etree.fromstring(ET.tostring(root, encoding='utf-8').decode('utf-8'))
            afile.write(etree.tostring(xmlString, pretty_print=True, encoding='utf-8'))