import dropbox
import os
import argparse
from unittest.mock import patch, MagicMock
import dropbox.exceptions

API_KEY = 'o8afup9dmesp1hl'
API_SECRET = 'hrsjhx4ilb8unib'
ACCESS_TOKEN = 'sl.B2m9iBcwqDcXYF-wQxoudoaxNJnExQ05XurQuzrMWfmEM3gayGbt-p9p6pUaSQr_t1QTv61cTxMUCxw2XxoMFCS1W23W7gFfp7A5yek6cu1UYxSUgxRMCbPLWI-_wsX-nDYqte7emSWOCyDsrOAr'  # You can generate this from your Dropbox app settings

# MAIN FUNCTIONALITY

def authenticate_dropbox(api_key, api_secret):
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    return dbx

def upload_file_to_dropbox(dbx, file_path, dropbox_path):
    try:
        with open(file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path)
        return "SUCCESS", f"The File was uploaded to {file_path}"
    except FileNotFoundError:  
        return "FAILURE, File not found!", None
    except dropbox.exceptions.ApiError as err:
        return "FAILURE, API error! - {err}", None

def list_main_directories(dbx):
    try:
        result = dbx.files_list_folder('')
        directories = [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FolderMetadata)]
        return "SUCCESS", directories
    except dropbox.exceptions.ApiError as err:
        print(f"API error: {err}")
        return "FAILURE", []

def list_subdirectories(dbx, path, level=1):
    subdirs = []
    try:
        if path == "/":
            path = ""
        result = dbx.files_list_folder(path)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                subdirs.append(entry.path_lower)
                status, subdir_entries = list_subdirectories(dbx, entry.path_lower, level+1)
                if status == "SUCCESS":
                    subdirs.extend(subdir_entries)
                else:
                    return status, subdirs
    except dropbox.exceptions.ApiError as err:
        return f"FAILURE: API error at path {path} - {err}", []
    return "SUCCESS", subdirs

def push_file_to_directory(dbx, file_path, directory_path):
    try:
        with open(file_path, 'rb') as f:
            dropbox_path = f"{directory_path}/{os.path.basename(file_path)}"
            dbx.files_upload(f.read(), dropbox_path)
            return "SUCCESS", f"File uploaded to {dropbox_path}"
    except FileNotFoundError:
        return "FAILURE: File not found", None
    except dropbox.exceptions.ApiError as err:
        return f"FAILURE: API error - {err}", None

def list_files_in_directory(dbx, directory_path):
    try:
        result = dbx.files_list_folder(directory_path)
        files_info = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                file_info = {
                    'name': entry.name,
                    'size': entry.size,
                    'extension': os.path.splitext(entry.name)[1]
                }
                files_info.append(file_info)
        return "SUCCESS", files_info
    except dropbox.exceptions.ApiError as err:
        print(f"API error at path {directory_path}: {err}")
        return "FAILURE", []

def retrieve_file_from_directory(dbx, dropbox_file_path, local_directory):
    try:
        metadata, res = dbx.files_download(dropbox_file_path)
        local_path = os.path.join(local_directory, metadata.name)
        with open(local_path, 'wb') as f:
            f.write(res.content)
        return "SUCCESS", f"File downloaded to {local_path}"
    except dropbox.exceptions.ApiError as err:
        return f"FAILURE: API error - {err}", None


def create_subdirectory(dbx, directory_path):
    try:
        dbx.files_create_folder_v2(directory_path)
        return "SUCCESS", f"Directory created at {directory_path}"
    except dropbox.exceptions.ApiError as err:
        return f"FAILURE: API error creating directory at {directory_path} - {err}", None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dropbox CLI")
    parser.add_argument("command", choices=["upload", "list_main_dirs", "list_subdirs", "push_file", "list_files", "retrieve_file", "create_subdir", "run_tests"])
    parser.add_argument("--local_file_path", type=str, help="Local file path for upload or retrieval")
    parser.add_argument("--dropbox_path", type=str, help="Dropbox path for upload, push_file, or retrieve_file")
    parser.add_argument("--directory_path", type=str, help="Directory path for listing subdirs, listing files, or creating subdir")
    parser.add_argument("--subdir_path", type=str, help="Path of the subdirectory to create")
    
    args = parser.parse_args()

    dbx = authenticate_dropbox(API_KEY, API_SECRET)

    if args.command == "upload":
        if args.local_file_path and args.dropbox_path:
            upload_file_to_dropbox(dbx, args.local_file_path, args.dropbox_path)
        else:
            print("Please provide --local_file_path and --dropbox_path")
    
    elif args.command == "list_main_dirs":
        directories = list_main_directories(dbx)
        if directories:
            print("Main Directories in your Dropbox:")
            for directory in directories:
                print(f"- {directory}")
    
    elif args.command == "list_subdirs":
        if args.directory_path:
            subdirectories = list_subdirectories(dbx, args.directory_path)
            if subdirectories:
                print(f"Subdirectories in '{args.directory_path}':")
                for subdir in subdirectories:
                    print(f"  - {subdir}")
            else:
                print(f"No subdirectories found in '{args.directory_path}'")
        else:
            print("Please provide --directory_path")
    
    elif args.command == "push_file":
        if args.local_file_path and args.dropbox_path:
            push_file_to_directory(dbx, args.local_file_path, args.dropbox_path)
        else:
            print("Please provide --local_file_path and --dropbox_path")
    
    elif args.command == "list_files":
        if args.directory_path:
            files_info = list_files_in_directory(dbx, args.directory_path)
            if files_info:
                print(f"Files in '{args.directory_path}':")
                for file_info in files_info:
                    print(f"Name: {file_info['name']}, Size: {file_info['size']} bytes, Extension: {file_info['extension']}")
            else:
                print(f"No files found in '{args.directory_path}'")
        else:
            print("Please provide --directory_path")
    
    elif args.command == "retrieve_file":
        if args.dropbox_path and args.local_file_path:
            retrieve_file_from_directory(dbx, args.dropbox_path, args.local_file_path)
        else:
            print("Please provide --dropbox_path and --local_file_path")
    
    elif args.command == "create_subdir":
        if args.subdir_path:
            create_subdirectory(dbx, args.subdir_path)
        else:
            print("Please provide --subdir_path")