import requests
import re
from lxml import etree
import sys
import argparse

input_file = 'epg_data.xml'
cleaned_file = 'cleaned_epg_data.xml'
output_file = 'filtered_epg_data.xml'

def downloadEPG(username, password):
    url = f"http://line.empire-4k.cc/xmltv.php?username={username}&password={password}"
    local_filename = "epg_data.xml"

    # Send a GET request to the URL
    response = requests.get(url)

    # Save the content to a local file
    with open(input_file, 'wb') as file:
        file.write(response.content)

    print(f"File downloaded and saved as {input_file}")

def remove_script_tags(input_file, cleaned_file):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        content = infile.read()

    # Remove all <script>...</script> tags
    cleaned_content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)

    with open(cleaned_file, 'w', encoding='utf-8') as outfile:
        outfile.write(cleaned_content)

    print(f"All <script> tags have been removed and the cleaned content is saved as '{cleaned_file}'.")

def validate_cleaned_xml(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            tree = etree.fromstring(content)
            print(f"XML file '{file_path}' is well-formed and valid.")
    except etree.XMLSyntaxError as e:
        print(f"XML file '{file_path}' is not well-formed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def filter_us_channels(input_file, output_file):
    try:
        with open(input_file, 'rb') as file:
            content = file.read()
            tree = etree.fromstring(content)

            # Find all channel elements
            channels = tree.findall('.//channel')
            # Find all programme elements
            programmes = tree.findall('.//programme')

            # Filter channels with "US ▎" in display-name and non-blank ID
            us_channel_ids = {channel.get('id') for channel in channels if channel.get('id') and "US ▎" in channel.find('display-name').text}

            # Remove channels not in the US list
            for channel in channels:
                if channel.get('id') not in us_channel_ids:
                    channel.getparent().remove(channel)

            # Remove programmes not linked to US channels
            for programme in programmes:
                if programme.get('channel') not in us_channel_ids:
                    programme.getparent().remove(programme)

            # Write the filtered XML to a new file
            with open(output_file, 'wb') as output:
                output.write(etree.tostring(tree, pretty_print=True, encoding='utf-8'))

            print(f"Filtered channels saved to '{output_file}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()

    #Download the EPG Source
    downloadEPG(args.username, args.password)

    #Remove <script> tags
    remove_script_tags(input_file, cleaned_file)

    #Validate the cleaned XML
    validate_cleaned_xml(cleaned_file)

    #Filter down to just US EPG Data
    filter_us_channels(cleaned_file, output_file)

if __name__ == "__main__":
    main()