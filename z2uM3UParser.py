from lxml import etree
import requests
import argparse

keywords = ["ABC KMGH DENVER","CBS 4 DENVER","NBC 9 DENVER CO","Sportsnet", "Max Sport", "Balley Sports", " Sky Sport", "HBO ", "Disney", "Discovery", "Cinemax", "Altitude Sports", "NHL", "NFL", "NBA", "ESPN", "Nickelodeon", "Showtime", "Starz", "SYFY", "USA Network", "TNT", "Animal Planet", "FOX HD", "FOX SPORTS","FOX SOCCER", "BBC", "NATIONAL GEOGRAPHIC", "CRIME & INVESTIGATION", "DIY NETWORK", "AMERICAN HORRORS", "DESTINATION AMERICA","HISTORY HD","SPIKE/PARAMOUNT", "PARAMOUNT NETWORK HD","History","Wild Earth","HALLMARK CHANNEL", "HALLMARK DRAMA","HALLMARK MOVIES & MYSTERIES","SCREENPIX","AMC","FX HD","FXX HD","SONY MOVIE","MGM+","MOVIE PLEX","CINE LIFE","LIFETIME MOVIE NETWORK","LIFETIME HD","COMEDY CENTRAL HD","SMITHSONIAN","NASA","TRU TV","HGTV","TBC","TLC","ADULT SWIM","COMEDY TV","A&E","BRAVO","ION TV","CARTOON NETWORK","PBS CA LOS ANGELES","MTV","MC MUSIC","GAME SHOW NETWORK","UFC","Red Bull","NBC SPORTS","PAC-12","Motortrend HD", "Motortrend FHD", "Motortrend SD","Fubo Sports","Root Sports","FORENSIC FILES"]  # Replace with your actual keywords
input_file = 'downloaded_file.m3u'
output_file = 'out.m3u'
epg_file = 'filtered_epg_data.xml'

# Convert keywords to lowercase
keywords = [keyword.lower() for keyword in keywords]

def downloadM3UFile(user, password):
    url = f"https://line.empire-4k.cc/get.php?username={user}&password={password}&type=m3u&output=mpegts"

    # Send a GET request to the URL
    response = requests.get(url)

    # Save the content to a local file
    with open(input_file, 'wb') as file:
        file.write(response.content)

    print(f"File downloaded and saved as {input_file}")

def narrowDownChannels():
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        lines = infile.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].lower()
            # Check to make sure these item do not exist in the string
            if "replay" not in line and "original" not in line:
                # Check for "#EXTINF:-1,US" and keywords, Special exemption for adding a colorado avalanche specific channel
                if "#extinf:-1,us" in line and any(keyword in line for keyword in keywords):
                    outfile.write(lines[i])  # Write the original line
                    if i + 1 < len(lines):
                        outfile.write(lines[i + 1])
                    i += 1  # Skip the next line as it is already written
            i += 1

    print("Processing complete. Check the output file for results.")

def fixTVGIDs():
    try:
        with open(epg_file, 'rb') as file, open(output_file, 'r', encoding='utf-8', errors='ignore') as m3uFile, open("upgraded.m3u", 'w', encoding='utf-8') as outfile:
            content = file.read()
            m3uLines = m3uFile.readlines()
            tree = etree.fromstring(content)

            # Find all channel elements
            channels = tree.findall('.//channel')


            i = 0
            while i < len(m3uLines):
                m3uLine = m3uLines[i].lower()
            
                matchFound = 0
                for channel in channels:
                    displayNameLower = channel.find('display-name').text.lower()
                    displayName = channel.find('display-name').text
                    id = channel.get('id')

                    if displayNameLower in m3uLine:
                        outfile.write(f"#EXTINF:-1 tvg-id=\"{id}\" tvg-name=\"{displayName}\", {displayName}\n")
                        if i + 1 < len(m3uLines):
                            outfile.write(m3uLines[i + 1])
                        matchFound = 1
                        break#Break out of this loop so duplicates aren't found
                
                if matchFound == 0:
                    outfile.write(m3uLines[i])
                    if i + 1 < len(m3uLines):
                        outfile.write(m3uLines[i + 1])
                i += 2
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()

    print("Downloading Z2U M3U File...")
    # downloadM3UFile(args.username, args.password)

    print("Narrowing down the channels list...")
    narrowDownChannels()
    
    print("Fixing tvgids...")
    fixTVGIDs()

if __name__ == "__main__":
    main()