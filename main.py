import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import argparse
import json
import re


SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    parser = argparse.ArgumentParser(description='Get input file path')
    parser.add_argument('file_path', type=str, help='input file path')
    args = parser.parse_args()

    # Reading shift data from json file
    f = open(args.file_path)
    schedule = json.load(f)
    f.close()

    # Read date
    date = schedule["Date"]
    # remove the date so that only shift data remains to iterate through
    del schedule["Date"]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print("credsnotvalids")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        venue_color = 0

        # Iterate through the venues
        for venue_name, shift_list in schedule.items():
            venue_color = venue_color % 11
            venue_color += 1
            # Iterate through the shifts
            for s in shift_list:
                # Each shift will create to events, checkin and checkout
                checkin_time, checkout_time = re.findall(r'(\d+:\d+)-(\d+:\d+)', s)[0]

                checkin_event = {
                    'summary': f"{venue_name} Checkin",
                    'start': {
                        'dateTime': f'{date}T{checkin_time}:00-06:00',
                        'timeZone': 'America/Denver',
                    },
                    'end': {
                        'dateTime': f'{date}T{checkin_time}:00-06:00',
                        'timeZone': 'America/Denver',
                    },
                    'colorId': venue_color
                }

                checkout_event = {
                    'summary': f"{venue_name} Checkout",
                    'start': {
                        'dateTime': f'{date}T{checkout_time}:00-06:00',
                        'timeZone': 'America/Denver',
                    },
                    'end': {
                        'dateTime': f'{date}T{checkout_time}:00-06:00',
                        'timeZone': 'America/Denver',
                    },
                    'colorId': venue_color
                }

                event = service.events().insert(calendarId='primary', body=checkin_event).execute()
                print('Check In Event created: %s' % (event.get('htmlLink')))

                event = service.events().insert(calendarId='primary', body=checkout_event).execute()
                print('Check Out Event created: %s' % (event.get('htmlLink')))

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
