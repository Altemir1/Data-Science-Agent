import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any, List, Union
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseUpload


def describe(df: pd.DataFrame) -> Union[str, Dict[str, Dict[str, float]]]:
    """
    Generate statistical description of the dataset.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze

    Returns:
        Union[str, Dict[str, Dict[str, float]]]: Statistical description including count, mean, std, min, max, and quartiles.
        Returns error message string if no dataset is provided.
    """
    if df is None:
        return "No dataset uploaded."
    return df.describe().to_dict()


def missing_values(df: pd.DataFrame) -> Union[str, Dict[str, int]]:
    """
    Analyze missing values in the dataset.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze

    Returns:
        Union[str, Dict[str, int]]: Dictionary with column names as keys and number of missing values as values.
        Returns error message string if no dataset is provided.
    """
    if df is None:
        return "No dataset uploaded."
    return df.isnull().sum().to_dict()


def get_info(df: pd.DataFrame) -> str:
    """
    Get detailed information about the dataset.

    Args:
        df (pd.DataFrame): Input DataFrame to analyze

    Returns:
        str: String containing DataFrame information including dtypes, non-null counts, and memory usage.
        Returns error message string if no dataset is provided.
    """
    if df is None:
        return "No dataset uploaded."
    buf = StringIO()
    df.info(buf=buf)
    return buf.getvalue()


def create_spreadsheet(sheets_service: Resource, title: str) -> Optional[str]:
    """
    Create a new Google Spreadsheet.

    Args:
        sheets_service (Resource): Google Sheets API service instance
        title (str): Title for the new spreadsheet

    Returns:
        Optional[str]: Spreadsheet ID if successful, None if failed
    """
    try:
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        request = sheets_service.spreadsheets().create(body=spreadsheet)
        response = request.execute()
        return response.get('spreadsheetId')
    except Exception as e:
        print(f"Error creating spreadsheet: {str(e)}")
        return None


def upload_to_drive(drive_service: Resource,
                    file_path: str,
                    mime_type: str,
                    folder_id: Optional[str] = None) -> Optional[str]:
    """
    Upload a file to Google Drive.

    Args:
        drive_service (Resource): Google Drive API service instance
        file_path (str): Path to the file to upload
        mime_type (str): MIME type of the file (e.g., 'text/csv', 'application/vnd.ms-excel')
        folder_id (Optional[str]): ID of the folder to upload to. If None, uploads to root

    Returns:
        Optional[str]: File ID if successful, None if failed
    """
    try:
        file_metadata = {'name': file_path.split('/')[-1]}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        with open(file_path, 'rb') as file:
            media = MediaIoBaseUpload(file,
                                      mimetype=mime_type,
                                      resumable=True)
            file = drive_service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()
        return file.get('id')
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None


def write_to_sheet(sheets_service: Resource,
                   spreadsheet_id: str,
                   data: List[List[Any]],
                   range_name: str = 'Sheet1!A1') -> bool:
    """
    Write data to a Google Spreadsheet.

    Args:
        sheets_service (Resource): Google Sheets API service instance
        spreadsheet_id (str): ID of the target spreadsheet
        data (List[List[Any]]): 2D array of data to write
        range_name (str): A1 notation of the range to write to

    Returns:
        bool: True if successful, False if failed
    """
    try:
        body = {
            'values': data
        }
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body).execute()
        return True
    except Exception as e:
        print(f"Error writing to sheet: {str(e)}")
        return False


def read_sheet(sheets_service: Resource,
               spreadsheet_id: str,
               range_name: str = 'Sheet1') -> Optional[pd.DataFrame]:
    """
    Read data from a Google Spreadsheet into a pandas DataFrame.

    Args:
        sheets_service (Resource): Google Sheets API service instance
        spreadsheet_id (str): ID of the spreadsheet to read
        range_name (str): A1 notation of the range to read

    Returns:
        Optional[pd.DataFrame]: DataFrame containing the sheet data if successful, None if failed
    """
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name).execute()
        values = result.get('values', [])

        if not values:
            return None

        # Assume first row as headers
        headers = values[0]
        data = values[1:]

        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        print(f"Error reading sheet: {str(e)}")
        return None


def list_files(drive_service: Resource,
               folder_id: Optional[str] = None,
               file_type: Optional[str] = None) -> List[Dict[str, str]]:
    """
    List files in Google Drive, optionally filtered by folder and file type.

    Args:
        drive_service (Resource): Google Drive API service instance
        folder_id (Optional[str]): ID of the folder to list files from. If None, lists from root
        file_type (Optional[str]): MIME type to filter by (e.g., 'application/vnd.google-apps.spreadsheet')

    Returns:
        List[Dict[str, str]]: List of dictionaries containing file information (id, name, mimeType)
    """
    try:
        query = []
        if folder_id:
            query.append(f"'{folder_id}' in parents")
        if file_type:
            query.append(f"mimeType='{file_type}'")

        query_string = ' and '.join(query) if query else ''

        results = []
        page_token = None

        while True:
            response = drive_service.files().list(
                q=query_string,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token).execute()

            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')

            if not page_token:
                break

        return results
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return []
