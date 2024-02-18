from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import io
import os

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
        print(f'\tSuccessfully uploaded file {file}')
        return 0
    except Exception as e: 
        print(f'\tError occurred when trying to upload {fpath} under {dst_fname}: \n\t{e}')
        return 1

# Delete all files by given fname
# Return 1 on failure, 0 on success
def delete_by_fname(fname):
    deleted = []
    try: 
        for id in name_map[fname]:
            service.files().delete(fileId=id).execute()
            deleted.append(id)
            print(f'\tSuccessfully delete file of id = {id}')
        #delete ids from name_map
        del name_map[fname]
        return 0
    except Exception as e:
            print(e)
            return 1

# Download all files of fname locally
def download(fname): 
    if name_map.get(fname) == None: 
        print("\tNo such file exists")
    try: 
        num_instances = len(name_map[fname])
        for i in range(0, num_instances):
            fid = name_map[fname][i]
            request_file = service.files().get_media(fileId=fid)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request_file)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f'\tDownload {int(status.progress() * 100)}.')

            save_name = ""
            if num_instances == 1: 
                save_name = fname
            else: 
                frags = fname.split('.')
                frags.insert(-1, '_' + str(i))
                save_name = ''.join(frags[:-1]) + '.' + frags[-1]
                print(f'\tSaved as {save_name}')
            
            file_retrieved: str = file.getvalue()
            with open(f"{save_name}", 'wb') as f:
                f.write(file_retrieved)
            print(f"Saved as {save_name}")
    except HttpError as error:
        print(f'\tAn error occurred: {error}')

# If directly running this script instead of importing, can use as cmdline cloud 'shell' 
if __name__ == '__main__':
    print("######################### GOOGLE DRIVE SHELL ###############################") 
    print("'help' for help\n'quit' to exit shell\n")
    cmd = ""
    while cmd != "exit":
        inpt = input("Enter command: ").split(" ")
        cmd = inpt[0]
        match cmd: 
            case "help": 
                pass 
            case "ls": 
                for k in name_map.keys():
                    print(f"\t{k}: {len(name_map[k])} instance(s)")
            case "upload": 
                if len(inpt) != 3:
                    print("\tSyntax error. Command should look like 'upload <dst filename> <filepath>")
                else: 
                    upload(inpt[1], inpt[2])
            case "del": 
                if len(inpt) != 2: 
                    print("\tSyntax erorr. Command should look like 'del <filename>'")
                else: 
                    delete_by_fname(inpt[1])
            case "download": 
                if len(inpt) != 2:
                    print("\tSyntax error. Command should look like 'download <filename>'")
                else: 
                    download(inpt[1])
            case "namemap":
                print(name_map)