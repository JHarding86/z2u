import sys
from lxml import etree
import requests

class epgTools:
    @staticmethod
    def filter_channels(input_file, output_file, keyword, needsChannelID):
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