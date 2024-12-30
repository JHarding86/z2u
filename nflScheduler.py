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
allNFL_m3u = "temp/NFL/nflall.m3u"

custom_m3u = "customNFL.m3u"

cleaned_file = 'temp/cleaned_epg_data.xml'
output_file = 'temp/NFL/nfl_epg_data.xml'

def main():
    print("Generating Custom M3U File...")
    parser = argparse.ArgumentParser(description='Process EPG data.')
    parser.add_argument('username', type=str, help='Username for the Z2U service')
    parser.add_argument('password', type=str, help='Password for the Z2U service')

    args = parser.parse_args()

    if os.path.isfile(custom_m3u):
        os.remove(custom_m3u)
    
    epgTools.createDirectory("temp/NFL")
    # print("Downloading M3U File...")
    # epgTools.downloadM3UFile(args.username, args.password, input_file)

    epgTools.filterM3UByKeywords(["NFL Game"], ["Network", "REPLAY"], input_file, allNFL_m3u)

    epgTools.filterEPGByKeywords(cleaned_file, output_file, "NFL", False)

    # Generate unique IDs so that we always have the same place to put different channels
    # unique_ids = epgTools.generate_unique_ids(80, 42)

    # createEPG(0)

    # tree = ET.ElementTree(root)
    # with open(custom_epg, 'wb') as afile:
    #     xmlString = etree.fromstring(ET.tostring(root, encoding='utf-8').decode('utf-8'))
    #     afile.write(etree.tostring(xmlString, pretty_print=True, encoding='utf-8'))
    # tree.write(custom_epg, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    main()