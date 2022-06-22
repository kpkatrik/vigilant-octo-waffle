import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1NZ5AmIJdbg0S96J9aY_7aa7_6c0UPrTgTrM0Ro4nH-0"
SHEET_NAME = "Database"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"


@st.experimental_singleton()
def connect_to_gsheet():
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[SCOPE],
    )

    # Create a new Http() object for every request
    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http()
        )
        return HttpRequest(new_http, *args, **kwargs)

    authorized_http = google_auth_httplib2.AuthorizedHttp(
        credentials, http=httplib2.Http()
    )
    service = build(
        "sheets",
        "v4",
        requestBuilder=build_request,
        http=authorized_http,
    )
    gsheet_connector = service.spreadsheets()
    return gsheet_connector


def get_data(gsheet_connector) -> pd.DataFrame:
    values = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:E",
        )
        .execute()
    )

    df = pd.DataFrame(values["values"])
    df.columns = df.iloc[0]
    df = df[1:]
    return df


def add_row_to_gsheet(gsheet_connector, row) -> None:
    gsheet_connector.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:E",
        body=dict(values=row),
        valueInputOption="USER_ENTERED",
    ).execute()


st.set_page_config(page_title="Bug report", page_icon="🐞", layout="centered")

st.title("🐞 Bug report!")

gsheet_connector = connect_to_gsheet()



form = st.form(key="annotation")

with form:
    cols = st.columns((1, 1))
    author = cols[0].text_input("Vem:")
    bug_type = cols[1].selectbox(
        "Typ av fel:", ["Front-end", "Back-end", "Data related", "404"], index=2
    )
    comment = st.text_area("Kommentar:")
    cols = st.columns(2)
    date = cols[0].date_input("När hände det:")
    bug_severity = cols[1].slider("Hur viktigt är det:", 1, 5, 2)
    submitted = st.form_submit_button(label="Submit")


if submitted:
    add_row_to_gsheet(
        gsheet_connector,
        [[author, bug_type, comment, str(date), bug_severity]],
    )
    st.success("Thanks! Your bug was recorded.")
    st.balloons()
