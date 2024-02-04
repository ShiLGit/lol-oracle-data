from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.errors import HttpError

#Create connection
scope = ['https://www.googleapis.com/auth/drive']
service_account_json_key = './secret/lol_oracle_jsonkey.json'
credentials = service_account.Credentials.from_service_account_file(
                              filename=service_account_json_key, 
                              scopes=scope)
service = build('drive', 'v3', credentials=credentials)



# Call the Drive v3 API
results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)").execute()
items = results.get('files', [])

print(items)
fid = '1zZfgZCxMPYO7oschzzBuIU2QHQEYs5O0'

## manual upload csv
# file_metadata = {'name': 'GOLD_III.csv'}
# media = MediaFileUpload('./GOLD_III.csv',
#                         mimetype='text/csv')


# file = service.files().create(body=file_metadata, media_body=media,
#                               fields='id').execute()

try: 
    request_file = service.files().get_media(fileId=fid)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request_file)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')

    file_retrieved: str = file.getvalue()
    with open(f"downloaded_file.csv", 'wb') as f:
        f.write(file_retrieved)
except HttpError as error:
    print(F'An error occurred: {error}')

