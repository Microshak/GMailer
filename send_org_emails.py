import time
import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import make_msgid
import gspread
import os
import argparse
from dotenv import load_dotenv

# --- NEW: Parse command-line argument for config selection ---
parser = argparse.ArgumentParser(description="Send emails using a selected config.")
parser.add_argument("profile", nargs="?", default="default", help="Profile to use (e.g., volunteer, donor)")
args = parser.parse_args()

# --- NEW: Load the appropriate .env file based on the argument ---
env_file = f".env.{args.profile}" if args.profile != "default" else ".env"
if not os.path.exists(env_file):
    raise FileNotFoundError(f"Config file '{env_file}' not found.")
load_dotenv(env_file)

# --- CONFIGURATION ---
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
OUTREACH_TRACKING_TAB = os.getenv("OUTREACH_TRACKING_TAB")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT")
EMAIL_HTML_FILE = os.getenv("EMAIL_HTML_FILE")
ATTACHMENT_FILE = os.getenv("ATTACHMENT_FILE")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
DELAY_BETWEEN_EMAILS = int(os.getenv("DELAY_BETWEEN_EMAILS", "1200"))
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

def get_gspread_client():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    return gc

def get_email_list():
    gc = get_gspread_client()
    sh = gc.open_by_url(GOOGLE_SHEET_URL)
    charities_ws = sh.worksheet(GOOGLE_SHEET_NAME)
    outreach_ws = sh.worksheet(OUTREACH_TRACKING_TAB)

    # Get all email addresses from Filtered Charities, column F (index 6)
    charities_data = charities_ws.get_all_values()
    email_list = []
    charity_names = []
    for row in charities_data[1:]:  # Skip header
        email = row[5].strip() if len(row) > 5 else ""
        name = row[1].strip() if len(row) > 1 else ""
        if email:
            email_list.append(email)
            charity_names.append(name)

    # Get all previously contacted emails from Outreach Tracking, column C (index 3)
    outreach_data = outreach_ws.get_all_values()
    contacted_emails = set()
    for row in outreach_data[1:]:  # Skip header
        if len(row) > 2:
            contacted_emails.add(row[2].strip())

    # Filter out emails already contacted and those with stop words in the name
    stop_words = [
        "pta", "ptsa", "sport", "soccer", "festival", "russian", "hindu", "christian", "jewish",
        "ball", "school", "booster", "grange", "tennis", "farm", "teacher", "pto", "derby", "china",
        "friend", "sanctuary", "lake", "kiwanis", "bbb", "city", "guild", "alliance", "ministry",
        "ministries", "society", "histor", "nnana", "hs", "bbq", "club", "choir", "trust", "pony",
        "horse", "scout", "church", "temple", "meditation", "center", "academy", "prayer", "heal",
        "christ", "foundation", "linux", "evangel", "ministr", "theater", "pentecostal", "holy",
        "college", "nieghborhood", "council", "home", "chorale", "cities","P.T.A.", "P.T.S.A.","riding",
        "dance", "parent", "lutheran", "lutheran", "baptist", "catholic", "evangelical","music", "police",
        "fire", "faith"
    ]
    filtered_emails = []
    filtered_names = []
    for name, email in zip(charity_names, email_list):
        if (
            email not in contacted_emails
            and not any(word in name.lower() for word in stop_words)
        ):
            filtered_emails.append(email)
            filtered_names.append(name)
    print(f"{len(filtered_emails)} emails based on criteria.")
    return filtered_names, filtered_emails

def send_email(to_email, html_body, attachment_path):
    msg = EmailMessage()
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.set_content("This email requires an HTML-compatible email client.")
    msg.add_alternative(html_body, subtype="html")

    # Attach sgc.png inline
    with open("sgc.png", "rb") as img:
        img_data = img.read()
        msg.get_payload()[1].add_related(
            img_data,
            maintype="image",
            subtype="png",
            cid="sgc.png"
        )

    if attachment_path not in [None, ""]:
        if attachment_path:
            ctype, encoding = mimetypes.guess_type(attachment_path)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(attachment_path, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=attachment_path)

    # Send email via Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

def log_outreach(name, email):
    # Log outreach to the Outreach Tracking tab: [name, "Mike", email]
    gc = get_gspread_client()
    sh = gc.open_by_url(GOOGLE_SHEET_URL)
    outreach_ws = sh.worksheet(OUTREACH_TRACKING_TAB)
    outreach_ws.append_row([name, "Mike", email])

if __name__ == "__main__":
    # Step 1: Gather emails
    names, emails = get_email_list()
   # print("Emails to contact:", emails)

    # Step 2: Read HTML template
    with open(EMAIL_HTML_FILE, "r", encoding="utf-8") as f:
        html_body = f.read()

    # Step 3: Send emails one at a time with delay
    for name, email in zip(names, emails):
        print(f"Sending to {email}...")
        try:
            send_email(email, html_body, ATTACHMENT_FILE)
            log_outreach(name, email)
            print(f"Sent to {email}. Waiting {DELAY_BETWEEN_EMAILS // 60} minutes before next send.")
        except:
            print(f'It failed on {email}')
            time.sleep(DELAY_BETWEEN_EMAILS)
        time.sleep(DELAY_BETWEEN_EMAILS)
        
        