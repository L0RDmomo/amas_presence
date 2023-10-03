import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from os.path import isfile

from matchmaking import PlayerRoleMMR, valid_roles


GSHEET_URL = "https://docs.google.com/spreadsheets/d/1b0zqKvwaEv-Wpf9KvUgelN0junAzEVFQrh7Iz7NPv3Y/edit#gid=13630990"


def fetch_google_sheet_data(sheet_url, page_title, auth_token):
    # Use the authentication token to create credentials
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        auth_token, ["https://spreadsheets.google.com/feeds"]
    )

    # Use the credentials to authorize gspread
    client = gspread.authorize(credentials)

    # Open the Google Spreadsheet using its URL
    spreadsheet = client.open_by_url(sheet_url)

    # Select the page by its title
    page = spreadsheet.worksheet(page_title)

    # Fetch all the data from the page
    data = page.get_all_values()

    return data


def convert_fetched_data_to_objs(data, form_data):
    objs = []
    errs = []

    player_roles = {
        "solo": "solo",
        "jungle": "jg",
        "mid": "mid",
        "support": "support",
        "carry": "carry",
    }
    player_roles_map = {
        x[2].lower(): {
            "main_role": player_roles[x[5].lower().strip()],
            "allowed_roles": [player_roles[y.lower().strip()] for y in x[6].split(", ")]
            + [player_roles[x[5].lower().strip()]],
        }
        for x in form_data
        if not (x[5] == "" and x[6] == "")
    }

    for row in data[3:]:
        ign = row[3].lower()

        player_mmr = {
            "carry": int(row[7]),
            "support": int(row[10]),
            "mid": int(row[13]),
            "jg": int(row[16]),
            "solo": int(row[19]),
        }
        try:
            player_roles = player_roles_map[ign]
        except KeyError as e:
            estring = f"could not find {e}"
            print(estring)
            errs.append(estring)
            continue

        for role in valid_roles:
            if role in player_roles["allowed_roles"]:
                objs.append(
                    PlayerRoleMMR(
                        ign, role, player_mmr[role], role == player_roles["main_role"]
                    )
                )

    return objs, errs


def get_discord_id_to_ign_map(auth_token_path, id_data):
    if isfile("form_data_dump.json"):
        with open("form_data_dump.json", "r") as f:
            form_data = json.load(f)
    else:
        form_data = fetch_google_sheet_data(
            GSHEET_URL, "Season 1 Form", auth_token_path
        )[1:]
        with open("form_data_dump.json", "w+") as f:
            json.dump(form_data, f)

    discord_nickname_to_ign = {}
    for r in form_data:
        discord_nickname_to_ign[r[3].lower()] = r[2]

    discord_id_to_ign = {}
    unfound_members = []
    for member in id_data:
        if member["nickname"].lower() in discord_nickname_to_ign:
            discord_id_to_ign[member["id"]] = discord_nickname_to_ign[
                member["nickname"].lower()
            ]
        else:
            unfound_members.append(member["nickname"])

    return discord_id_to_ign, unfound_members


def sync(auth_token_path):
    data = fetch_google_sheet_data(GSHEET_URL, "All Divisions", auth_token_path)
    with open("data_dump.json", "w+") as f:
        json.dump(data, f)

    form_data = fetch_google_sheet_data(GSHEET_URL, "Season 1 Form", auth_token_path)[
        1:
    ]
    with open("form_data_dump.json", "w+") as f:
        json.dump(form_data, f)

    objs, errs = convert_fetched_data_to_objs(data, form_data)
    with open("objs_dump.json", "w+") as f:
        json.dump([x.__dict__ for x in objs], f)

    return errs


def get_objs(auth_token_path):
    if isfile("data_dump.json"):
        with open("data_dump.json", "r") as f:
            data = json.load(f)
    else:
        data = fetch_google_sheet_data(GSHEET_URL, "All Divisions", auth_token_path)
        with open("data_dump.json", "w+") as f:
            json.dump(data, f)

    if isfile("form_data_dump.json"):
        with open("form_data_dump.json", "r") as f:
            form_data = json.load(f)
    else:
        form_data = fetch_google_sheet_data(
            GSHEET_URL, "Season 1 Form", auth_token_path
        )[1:]
        with open("form_data_dump.json", "w+") as f:
            json.dump(form_data, f)

    if isfile("objs_dump.json"):
        with open("objs_dump.json", "r") as f:
            objs = json.load(f)
            objs = [
                PlayerRoleMMR(
                    player_id=x["player_id"],
                    role=x["role"],
                    mmr=x["mmr"],
                    primary_role=x["primary_role"],
                )
                for x in objs
            ]
    else:
        objs = convert_fetched_data_to_objs(data, form_data)
        with open("objs_dump.json", "w+") as f:
            json.dump([x.__dict__ for x in objs], f)

    return objs


if __name__ == "__main__":
    get_objs()
