# dataexport.py
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
from constants import SHEETS_EMAIL_ADDRESS


# Create a google sheet and share with another user
def create_sheet_and_drive(spreadsheet_service, drive_service):
    spreadsheet_details = {
        "properties": {
            "title": "telegrambot_" + datetime.datetime.now().strftime("%Y-%m-%d"),
        }
    }
    sheet = (
        spreadsheet_service.spreadsheets()
        .create(body=spreadsheet_details, fields="spreadsheetId")
        .execute()
    )
    sheetId = sheet.get("spreadsheetId")
    permission1 = {
        "type": "user",
        "role": "writer",
        "emailAddress": SHEETS_EMAIL_ADDRESS,
    }
    drive_service.permissions().create(fileId=sheetId, body=permission1).execute()
    return sheetId


# Simple function to export a dataframe to a spreadsheet
def export_pandas_df_to_sheets(spreadsheet_service, df, spreadsheet_id):
    body = {"values": df.values.tolist()}

    result = (
        spreadsheet_service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            body=body,
            valueInputOption="USER_ENTERED",
            range="Sheet1",
        )
        .execute()
    )
    print("{0} cells appended.".format(result.get("updates").get("updatedCells")))
