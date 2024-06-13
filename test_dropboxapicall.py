import unittest
from unittest.mock import patch, MagicMock
import dropbox
import dropboxapicall
import os

class TestDropboxScript(unittest.TestCase):

    @patch('dropboxapicall.dropbox.Dropbox')  # Mock the Dropbox class
    def setUp(self, MockDropbox):
        # Create a mock Dropbox client
        self.mock_dbx = MockDropbox.return_value

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="file content")
    def test_upload_file_to_dropbox(self, mock_file):
        status, message = dropboxapicall.upload_file_to_dropbox(self.mock_dbx, 'local/path/file.txt', '/dropbox/path/file.txt')
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(message, "The File was uploaded to local/path/file.txt")
        self.mock_dbx.files_upload.assert_called_once()

    def test_list_main_directories(self):
        self.mock_dbx.files_list_folder.return_value.entries = [
            dropbox.files.FolderMetadata(name='dir1'),
            dropbox.files.FolderMetadata(name='dir2')
        ]
        status, directories = dropboxapicall.list_main_directories(self.mock_dbx)
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(directories, ['dir1', 'dir2'])

    def test_list_subdirectories(self):
        # Mock return values for different folder paths
        def mock_files_list_folder(path):
            if path == "/dir1":
                return MagicMock(entries=[
                    dropbox.files.FolderMetadata(path_lower='/dir1/subdir1'),
                    dropbox.files.FolderMetadata(path_lower='/dir1/subdir2')
                ])
            elif path == "/dir1/subdir1":
                return MagicMock(entries=[
                    dropbox.files.FolderMetadata(path_lower='/dir1/subdir1/subsubdir1')
                ])
            elif path == "/dir1/subdir2":
                return MagicMock(entries=[])
            elif path == "/dir1/subdir1/subsubdir1":
                return MagicMock(entries=[])
            else:
                return MagicMock(entries=[])
        
        self.mock_dbx.files_list_folder.side_effect = mock_files_list_folder
        
        status, subdirectories = dropboxapicall.list_subdirectories(self.mock_dbx, '/dir1')
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(subdirectories, ['/dir1/subdir1', '/dir1/subdir1/subsubdir1', '/dir1/subdir2'])

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="file content")
    def test_push_file_to_directory(self, mock_file):
        status, message = dropboxapicall.push_file_to_directory(self.mock_dbx, 'local/path/file.txt', '/dropbox/path')
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(message, "File uploaded to /dropbox/path/file.txt")
        self.mock_dbx.files_upload.assert_called_once()

    def test_list_files_in_directory(self):
        self.mock_dbx.files_list_folder.return_value.entries = [
            dropbox.files.FileMetadata(name='file1.txt', size=100),
            dropbox.files.FileMetadata(name='file2.pdf', size=200)
        ]
        status, files_info = dropboxapicall.list_files_in_directory(self.mock_dbx, '/directory')
        expected_files_info = [
            {'name': 'file1.txt', 'size': 100, 'extension': '.txt'},
            {'name': 'file2.pdf', 'size': 200, 'extension': '.pdf'}
        ]
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(files_info, expected_files_info)

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_retrieve_file_from_directory(self, mock_file):
        mock_response = MagicMock()
        mock_response.content = b'file content'
        mock_metadata = MagicMock()
        mock_metadata.name = 'file.txt'  # Explicitly set the name attribute
        
        self.mock_dbx.files_download.return_value = (mock_metadata, mock_response)
        
        status, message = dropboxapicall.retrieve_file_from_directory(self.mock_dbx, '/dropbox/path/file.txt', 'local\path')
        self.assertEqual(status, "SUCCESS")
        expected_message = f"File downloaded to {os.path.normpath(os.path.join('local', 'path', 'file.txt'))}"
        self.assertEqual(message, expected_message)
        mock_file.assert_called_once_with(os.path.normpath(os.path.join('local', 'path', 'file.txt')), 'wb')
        mock_file().write.assert_called_once_with(b'file content')

    def test_create_subdirectory(self):
        self.mock_dbx.files_create_folder_v2.return_value = MagicMock()
        status, message = dropboxapicall.create_subdirectory(self.mock_dbx, '/new_subdirectory')
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(message, "Directory created at /new_subdirectory")
        self.mock_dbx.files_create_folder_v2.assert_called_once_with('/new_subdirectory')

if __name__ == '__main__':
    unittest.main()