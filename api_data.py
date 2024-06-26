import random
from endpoints import *

username = "DEEKSHITH"
password = "Sirma@123"
notification_emails = ["deekshith.p@sirmaindia.com", "swaraj.m@sirmaindia.com", "iborg.automation@sirmaindia.com"]

folder_name = f"API_test_{random.randint(1, 100000)}"
cifID = random.randint(1, 10000)
pdf_file_name = "sample_test.pdf"
pdf_page_count = 10
updated_file_name = f"UpdatedTestingFile_{random.randint(1, 100000)}.pdf"
updated_folder_name = folder_name + f"_updated_{random.randint(1, 100000)}"
document_password = "A12345678"
old_tag = "OldTag"
new_tag = "NewTag"
new_remarks = "NewRemarks"
pdf_split_range = "1-5"
operation_types = [("range", "5-8", 4), ("random", "1,5,9", 3), ("single", "4", 1)]
actions = ['favourite', 'archive', 'trash']
file_formats = ["jpeg", "png", "doc", "txt", "docx", "xlsx", "tiff"]
search_filters = ["isEqualTo", "contains", "beginsWith", "endsWith", "notContains"]
workspace_field_names = ['blank_foldername', 'blank_filepath', 'character_limit', 'file_already_exists']
file_upload_field_names = ['blank_filepath', 'blank_foldername', 'blank_tag', 'blank_files', 'blank_remarks',
                           'invalid_workspacetype']
workspaces = ["AUTOWORKSPACE", "MANUALWORKSPACE"]
extensions = [".jpeg", ".png", ".doc", ".txt", ".docx", ".xlsx", ".tiff"]

password_validations = {
    "correct_password": (document_password, True),
    "wrong_password": ("123", False)
}

test_create_manualworkspace_directory_json = {
    "folderPath": f"/IDOC_Filesystem/workspace/manualworkspace/{folder_name}",
    "folderName": folder_name,
    "cifId": cifID
}

test_upload_data = {'filePath': f'/IDOC_Filesystem/workspace/manualworkspace/{folder_name}',
                    'workspaceType': 'manualworkspace',
                    'folderName': folder_name,
                    'passwordProtected': 'false',
                    'tags': old_tag,
                    'version': '1',
                    'remarks': 'BCD',
                    "cifId": cifID
                    }

test_upload_file = [
    ('files', (
        "sample_test.pdf",
        open("sample_test.pdf", 'rb'),
        'application/pdf')),
    ('files', (
        "sample_txt.txt",
        open("sample_txt.txt", 'rb'),
        'text/plain')),
    ('files', (
        "sample_tiff.tiff",
        open("sample_tiff.tiff", 'rb'),
        'image/tiff')),
    ('files', (
        "sample_xlsx.xlsx",
        open("sample_xlsx.xlsx", 'rb'),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
    ('files', (
        "sample_image.png",
        open("sample_image.png", 'rb'),
        'image/png')),
    ('files', (
        "dummy.pdf",
        open("dummy.pdf", 'rb'),
        'application/pdf'))
]

test_get_documents_params = {"filePath": f'/IDOC_Filesystem/workspace/manualworkspace/{folder_name}'}

test_search_manualworkspace_filename_params = {
    "searchOn": 'DOCUMENT',
    "field": "fileName",
    "filter": None,
    "workspace": None,
    "value": pdf_file_name,
    "operator": None,
    "size": 2000
}

test_search_manualworkspace_documentid_params = {
    "searchOn": "DOCUMENT",
    'workspace': None,
    'field': "documentId",
    'filter': None,
    'value': None,
    "operator": None,
    "size": 2000
}

test_search_manualworkspace_extension_params = {
    "searchOn": "DOCUMENT",
    'workspace': None,
    'field': "extension",
    'filter': None,
    'value': None,
    "operator": None,
    "size": 2000
}

test_search_manualworkspace_tags_params = {
    "searchOn": "DOCUMENT",
    'workspace': None,
    'field': "tags",
    'filter': None,
    'value': new_tag,
    "operator": None,
    "size": 2000
}

test_search_manualworkspace_folderpath_params = {
    "searchOn": "FOLDER",
    'workspace': None,
    'field': "folderPath",
    'filter': None,
    'value': f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}",
    "operator": None,
    "size": 2000
}

test_search_manualworkspace_foldername_params = {
    "searchOn": "FOLDER",
    'workspace': None,
    'field': "folderName",
    'filter': None,
    'value': updated_folder_name
}

test_search_manualworkspace_folderid_params = {
    "searchOn": "FOLDER",
    'workspace': None,
    'field': "folderId",
    'filter': None,
    'value': None,
    "operator": None,
    "size": 2000
}

test_update_file_name_json = {
    "id": None,
    "fileName": updated_file_name
}

test_update_folder_name_params = {"newFolderName": updated_folder_name}

test_update_file_tags_json = {
    "id": None,
    "oldTag": old_tag,
    "newTag": new_tag
}

test_update_file_remark_json = {
    "id": None,
    "remarks": new_remarks
}

test_update_file_is_verified_json = {
    "id": None,
    "isVerified": 'true'
}

test_update_file_password_json = {
    "id": None,
    "protectedPassword": "true",
    "password": document_password
}

test_update_file_all_fields = {}

test_audit_params = {
    "id": None
}

test_check_password_json = {
    "id": None,
    "password": None
}

test_make_file_fav_arch_trs_json = {
    "action": None,
    "resourceType": "document",
    "ids": [],
    "status": "true"
}
test_make_folder_fav_arch_trs_json = {
    "action": None,
    "resourceType": "folder",
    "ids": [],
    "status": "true"
}

test_get_all_fav_arch_trs_file_params = {
    "action": None,
    "resourceType": "document",
    "pageNo": 0,
    "pageSize": 2000
}

test_get_all_fav_arch_trs_folder_params = {
    "action": None,
    "resourceType": "folder",
    "pageNo": 0,
    "pageSize": 2000
}

test_delete_file_fav_arch_trs_json = {
    "ids": [],
    "type": "document"
}

test_delete_folder_fav_arch_trs_json = {
    "ids": [],
    "type": "folder"
}

test_convert_pdf_to_other_format_params = {
    "documentId": None,
    "format": None
}

test_pdf_split_params = {
    "documentId": None,
    "type": None,
    "range": None
}

test_pdf_rotate_params = {
    "documentId": None
}

test_pdf_compress_params = {
    "documentId": None
}

test_convert_text_file_to_pdf_params = {
    "documentId": None
}

test_convert_tiff_file_to_pdf_params = {
    "documentId": None
}

test_convert_image_to_pdf_params = {
    "documentId": None
}

test_convert_xlsx_file_to_pdf_params = {
    "documentId": None
}

test_merge_pdfs_params = {
    "documentId": None
}

test_download_zip_params = {
    "documentIds": None
}

api_data = {
    "create_manualworkspace_directory_api": {
        "url": create_directory_url,
        "data": test_create_manualworkspace_directory_json
    },
    "upload_file_api": {
        "url": upload_url,
        "data": test_upload_data
    }
}

test_cases = {
    "blank_foldername": ("folderName", "", "Folder name is required"),
    "blank_filepath": ("filePath", "", "File path is required"),
    "blank_tag": ("tags", "", "At least one tag must be provide"),
    "blank_files": ("files", [], "Files cannot be null"),
    "blank_remarks": ("remarks", "", "Remarks are required"),
    "invalid_workspaceType": ("workspaceType", "InvalidWorkSpace", "Invalid workspaceType field")
}

test_send_email_json = {
    "toEmails": ["deekshith.p@sirmaindia.com", "swaraj.m@sirmaindia.com", "iborg.automation@sirmaindia.com"],
    "filePath": [
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/{updated_file_name}",
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/dummy.pdf",
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/sample_image.png",
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/sample_tiff.tiff",
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/sample_txt.txt",
        f"/IDOC_Filesystem/workspace/manualworkspace/{updated_folder_name}/sample_xlsx.xlsx"
    ]
}
