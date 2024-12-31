import requests
import datetime
import json
import argparse
from epgTools import epgTools

input_file = "temp/downloaded_file.m3u"
allNFL_m3u = "temp/NFL/nflall.m3u"

custom_m3u = "customNFL.m3u"
custom_epg = "customNFL.xml"

cleaned_file = 'temp/cleaned_epg_data.xml'
output_file = 'temp/NFL/nfl_epg_data.xml'

def getJSON(url):
    response = requests.get(url)
    data = json.loads(response.text)
    return data

def getNFLSeasonURL():
    print("Getting the most recent season.")
    seasonURLs = getJSON("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons?limit=100")

    seasonURL = seasonURLs["items"][0]['$ref']
    return seasonURL

def getNFLYearWeekInfo(seasonURL):
    print("Getting Year Week Info.")
    seasonInfo = getJSON(seasonURL)
    yearWeekInfo = {}
    yearWeekInfo["year"] = seasonInfo["type"]["year"]
    yearWeekInfo["week"] = seasonInfo["type"]["week"]["number"]
    return yearWeekInfo

def getDate():
    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    return formatted_date
    
def getNFLWeeklySchedule():
    print("Gathering information needed to get the weekly schedule.")

    seasonURL = getNFLSeasonURL()
    yearWeekInfo = getNFLYearWeekInfo(seasonURL)
    print(f"Year: {yearWeekInfo['year']} | Week: {yearWeekInfo['week']}")

    print("Getting this weeks schedule.")
    schedule = getJSON(f"https://cdn.espn.com/core/nfl/schedule?xhr=1&year={yearWeekInfo['year']}&week={yearWeekInfo['week']}")

    return schedule["content"]["schedule"][f"{getDate()}"]["games"]

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()
    
    epgTools.createDirectory("temp/NFL")
    epgTools.filterM3UByKeywords(["NFL Game"], ["Network", "REPLAY"], input_file, allNFL_m3u)

    games = getNFLWeeklySchedule()

    parsedGames = []
    for game in games:
        matchup = game['name']
        teams = matchup.split(" at ")

        aGame = {}
        aGame["away"] = teams[0]
        aGame["home"] = teams[1]
        aGame["date"] = game['competitions'][0]['date']
        aGame['logo'] = "https://static.www.nfl.com/image/upload/v1554321393/league/nvfr7ogywskqrfaiu38m.svg"
        parsedGames.append(aGame)

        print(f"{aGame['away']} at {aGame['home']} @ {aGame['date']}")

    # Generate unique IDs so that we always have the same place to put different channels
    unique_ids = epgTools.generate_unique_ids(20, 12)

    epgTools.createEPG(parsedGames, unique_ids, allNFL_m3u, "NFL")

if __name__ == "__main__":
    main()