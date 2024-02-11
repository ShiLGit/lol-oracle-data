from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
import os
from googleapiclient.errors import HttpError

# Helper func
def dict_append(map, key, val):
    keys = map.keys()
    if key not in keys: 
        map[key] = [val]
    else: 
        map[key].append(val)

## INITIALIZE CONNECTION #################################################################################################
#Create connection
scope = ['https://www.googleapis.com/auth/drive']
service_account_json_key = './secret/lol_oracle_jsonkey.json'
credentials = service_account.Credentials.from_service_account_file(
                              filename=service_account_json_key, 
                              scopes=scope)
service = build('drive', 'v3', credentials=credentials)

# Get all files on the drive 
results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)").execute()
items = results.get('files', [])
name_map = dict() 

#Generate map {'filename': [list of ids under that file name]}
for r in results['files']:
    dict_append(name_map, r['name'], r['id'])
print(name_map)


## START OF ACTUAL UTIL FUNCTIONS ######################################################################################

# Upload file at fpath to google drive api as dst_fname 
# Return 1 on failure, 0 on success
def upload(dst_fname, fpath):
    file_metadata = {'name': f'{dst_fname}'}

    try: 
        media = MediaFileUpload(f'{fpath}')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        dict_append(name_map, dst_fname, file['id'])
        print(f'Successfully uploaded file {file}')
        return 0
    except Exception as e: 
        print(f'Error occurred when trying to upload {fpath} under {dst_fname}: \n\t{e}')
        return 1

# Delete all files by given fname
# Return 1 on failure, 0 on success
def delete_by_fname(fname):
    deleted = []
    try: 
        for id in name_map[fname]:
            service.files().delete(fileId=id).execute()
            deleted.append(id)
            print(f'Successfully delete file of id = {id}')
        #delete ids from name_map
        del name_map[fname]
        return 0
    except Exception as e:
            print(e)
            return 1
