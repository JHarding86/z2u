import requests
import re
from lxml import etree
import sys
import argparse
from epgTools import epgTools

input_file = 'epg_data-King.xml'
cleaned_file = 'cleaned_epg_data.xml'
output_file = 'filtered_epg_data.xml'

def downloadEPG(username, password):
    url = f"http://line.king-4k.cc/xmltv.php?username={username}&password={password}"
    # url = f"http://line.empire-4k.cc/xmltv.php?username={username}&password={password}"

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
    epgTools.filter_channels(cleaned_file, output_file, "US ▎", True)

if __name__ == "__main__":
    main()