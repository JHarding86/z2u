import sys
from lxml import etree
import requests
import random
import uuid
import os

class epgTools:
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
                    print(f"Progress: {percent:.2f}%")

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
    def generate_unique_ids(count, seed):
        random.seed(seed)
        ids = []
        for _ in range(count):
            id_str = str(uuid.UUID(int=random.getrandbits(128)))  # Generate a unique UUID
            ids.append(id_str)
        global unique_ids
        return ids
    
    @staticmethod
    def createDirectory(dir):
        # Check if the directory already exists
        if not os.path.exists(dir):
            os.makedirs(dir)
            print(f"Directory '{dir}' created successfully.")
        else:
            print(f"Directory '{dir}' already exists.")