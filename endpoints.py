# Base URL of the API
base_url = 'https://idocxapi.impactosuitedeveloper.com'

# endpoint URLs
# workspace
create_directory_url = base_url + "/api/v1/workspace/create-directory"
upload_url = base_url + "/api/v1/workspace/upload"
documents_url = base_url + "/api/v1/workspace/documents"
download_url = base_url + "/api/v1/workspace/download/{id}"
update_file_url = base_url + "/api/v1/workspace/update-file"
update_tag_url = base_url + "/api/v1/workspace/update-tags/{id}"
update_folder_url = base_url + "/api/v1/workspace/update-folder/{id}"
get_all_folder_structure_url = base_url + "/api/v1/workspace/{workSpaceName}"
auditing_url = base_url + "/api/v1/workspace/audit"
check_password_url = base_url + "/api/v1/workspace/protect"
flexcube_documents = base_url + "/api/v1/workspace/all-files/{cifID}"

# search
search_url = base_url + "/api/v1/search"

# fav,arch,trash
make_fav_arc_trs_url = base_url + "/v1/update"
get_all_fav_arc_trs_url = base_url + "/v1/list"

# delete
delete_fav_arc_trs_url = base_url + "/v1/delete-resource"

# pdf operations
pdf_to_other_format_url = base_url + "/v1/conversions/pdf-file"
pdf_split_url = base_url + "/v1/conversions/pdf-split"
pdf_remove_url = base_url + "/v1/conversions/pdf-remove"
pdf_rotate_url = base_url + "/v1/conversions/pdf-rotate"
pdf_compress_url = base_url + "/v1/conversions/pdf-compress"
text_file_to_pdf_url = base_url + "/v1/conversions/txt-pdf"
tiff_file_to_pdf_url = base_url + "/v1/conversions/tiff-pdf"
xlsx_file_to_pdf_url = base_url + "/v1/conversions/xlsx-pdf"
image_to_pdf_url = base_url + "/v1/conversions/image-pdf"
merge_pdf_url = base_url + "/v1/conversions/pdf-merger"
download_zip_url = base_url + "/v1/conversions/download-zip"

# notifications
send_email_url = base_url + "/v1/send-email"
drive_link_url = base_url + "/v1/drive-link"
