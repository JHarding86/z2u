import requests
import datetime
import json
import argparse
from epgTools import epgTools

input_file = "temp/downloaded_file.m3u"
allNHL_m3u = "temp/nhlall.m3u"
custom_m3u = "customNHL.m3u"
custom_epg = "customNHL.xml"

cleaned_file = 'temp/cleaned_epg_data.xml'
output_file = 'temp/nhl_epg_data.xml'

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
        return data
    print("JSON data has been parsed:")
    # print(json.dumps(data, indent=4))

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()
        
    print("Downloading M3U File...")
    epgTools.downloadM3UFile(args.username, args.password, input_file)

    epgTools.filterM3UByKeywords(["NHL"], ["Network", " : ", "REPLAY"], input_file, allNHL_m3u)

    print("Getting NHL Scheulde...")
    getNHLSchedule("temp/nhlSchedule.json")

    print("Parsing NHL Scheulde...")
    data = parseNHLScheduleToJSON("temp/nhlSchedule.json")

    games = data["gameWeek"][0]["games"]
    parsedGames = []

    for game in games:
        aGame = {}
        aGame["away"] = game["awayTeam"]["commonName"]["default"]
        aGame["logo"] = game["awayTeam"]["logo"]
        aGame["home"] = game["homeTeam"]["commonName"]["default"]
        aGame["date"] = game["startTimeUTC"]
        parsedGames.append(aGame)

    # Generate unique IDs so that we always have the same place to put different channels
    unique_ids = epgTools.generate_unique_ids(80, 42)

    epgTools.createEPG(parsedGames, unique_ids, allNHL_m3u, "NHL")

if __name__ == "__main__":
    main()