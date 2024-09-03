#!/usr/bin/env python

import requests
from pyquery import PyQuery
from datetime import datetime
import json
from flask import Flask

# Base URL for the new site
wiki = "https://www.theapplewiki.com"

# Function to construct the firmware keys page URL directly
def getFirmwareKeysPage(device, buildnum):
    # Define the codename mapping based on the device and build number
    codename = "StarlightG"  # Replace with actual logic to determine the codename if dynamic

    # Construct the URL based on the format
    pagelink = f"{wiki}/wiki/Keys:{codename}_{buildnum}_({device})"
    
    print(f"Constructed Page URL: {pagelink}")  # Debug output
    return pagelink

# Function to fetch and parse keys from the firmware keys page
def getkeys(device, buildnum):
    rsp = {}
    pagelink = getFirmwareKeysPage(device, buildnum)
    
    try:
        # Make a request to fetch the firmware keys page
        r = requests.get(pagelink)
        if r.status_code != 200:
            raise ValueError(f"Failed to fetch firmware keys page, status code: {r.status_code}")

        html = r.text
        print(f"Firmware Keys Page HTML: {html[:500]}...")  # Print a snippet of the HTML for debugging

        # Initialize the response dictionary
        rsp["identifier"] = device
        rsp["buildid"] = buildnum
        rsp["codename"] = pagelink.split(":")[-1].split("_")[0]
        rsp["updateramdiskexists"] = False
        rsp["restoreramdiskexists"] = False

        # Use PyQuery to parse the page content
        pq = PyQuery(html)
        keys = []
        for span in pq.items('span.mw-headline'):
            id = span.attr["id"]
            if id == "Update_Ramdisk":
                rsp["updateramdiskexists"] = True
            if id == "Restore_Ramdisk":
                rsp["restoreramdiskexists"] = True

            key = {}
            name = span.text()
            if name == "Root Filesystem":
                name = "RootFS"
            fname = span.parent().next("* > span.keypage-filename").text()

            name = name.replace(" ", "")
            try:
                iv = span.parent().siblings("*>*>code#keypage-" + name.lower() + "-iv").text()
                key_ = span.parent().siblings("*>*>code#keypage-" + name.lower() + "-key").text()
                kbag = span.parent().siblings("*>*>code#keypage-" + name.lower() + "-kbag").text()
            except:
                continue

            key["image"] = name
            key["filename"] = fname  # WARNING This may be in the wrong format
            key["date"] = datetime.now().isoformat()
            key["iv"] = iv
            key["key"] = key_
            key["kbag"] = kbag

            keys.append(key)
        rsp["keys"] = keys
        return json.dumps(rsp)
    except Exception as e:
        print(f"Error during fetching keys: {e}")
        return json.dumps({"error": str(e)})

app = Flask(__name__)

# Flask route to handle both formats of the request
@app.route("/firmware/<device>/<path:buildid>")
def keys(device, buildid):
    print(f"Getting keys for /{device}/{buildid}")
    
    # Normalize the request to handle duplicate 'device' parameters
    # Split the 'buildid' to extract the actual build number
    build_parts = buildid.split('/')
    
    # Handle the case where the buildid contains device again
    if len(build_parts) > 1 and build_parts[0] == device:
        buildid = build_parts[1]  # Normalize to the correct buildid
    
    # Fetch the firmware keys
    keys = getkeys(device, buildid)
    print(keys + "\n")
    return keys

if __name__ == "__main__":
    print("Running webserver")
    app.run(host='0.0.0.0', port=8888)
