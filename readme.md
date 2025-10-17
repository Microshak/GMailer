Volunteer

https://www.zeffy.com/en-US/ticketing/156667fc-154b-4fef-92ed-c28403997045

---

## How to Change the Google Sheet Source

This project uses a Google Sheet to get email addresses and track outreach.  
To change which Google Sheet is used:

1. **Edit the appropriate `.env` file**  
   Open the `.env`, `.env.volunteer`, or `.env.donor` file (depending on which profile you use).

2. **Update these variables:**
   - `GOOGLE_SHEET_URL` — The full URL of your Google Sheet.
   - `GOOGLE_SHEET_NAME` — The name of the worksheet/tab containing your email list.
   - `OUTREACH_TRACKING_TAB` — The name of the worksheet/tab used for tracking sent emails.

3. **Save the file.**

4. **Run the script with the desired profile:**  
   ```bash
   python3 send_org_emails.py volunteer
   ```
   or
   ```bash
   python3 send_org_emails.py sponsor
   ```

**Note:**  
Make sure your Google service account has access to the new Google Sheet.

