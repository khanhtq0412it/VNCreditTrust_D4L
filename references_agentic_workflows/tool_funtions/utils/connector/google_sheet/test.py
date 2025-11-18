from utils.connector.google_sheet.module import GoogleSheetClient
from utils.connector.google_sheet.providers import fetch_google_sheet_as_df, get_google_sheet_title

name = get_google_sheet_title(
    spreadsheet_id='1Y8cGGDTIFQDcxJp9BciDBXg7RiDYUSIBuIvzYqHkczQ'
)
print(name)