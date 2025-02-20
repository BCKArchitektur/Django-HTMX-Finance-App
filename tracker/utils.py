import os
import uuid

def generate_revit_shared_parameter_file(project):
    """Generate a Revit shared parameter file with project-specific details."""

    file_content = f"""# This is a Revit shared parameter file.
# Do not edit manually.
*META    VERSION    MINVERSION
META    2    1
*GROUP    ID    NAME
GROUP    1    Project Information
*PARAM    GUID    NAME    DATATYPE    DATACATEGORY    GROUP    VISIBLE    DESCRIPTION    USERMODIFIABLE    HIDEWHENNOVALUE
PARAM    {uuid.uuid4()}    BCK_Project Status    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Projektkürzel    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_BH_Straße    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Client Name    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Project Issue Date    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_IN_Mengen Kommentare    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Organizations Name    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Project Name    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Project Number    TEXT        1    1        1    0
PARAM    {uuid.uuid4()}    BCK_Organization Description    TEXT        1    1        1    0
"""

    # Replace placeholders with actual project details
    file_content = file_content.replace("BCK_Project Status", project.status)
    file_content = file_content.replace("BCK_Projektkürzel", project.project_no)
    file_content = file_content.replace("BCK_BH_Straße", project.project_address)
    file_content = file_content.replace("BCK_Client Name", project.client_name.client_name if project.client_name else "Unknown Client")
    file_content = file_content.replace("BCK_Project Issue Date", str(project.client_name.client_mail if project.client_name else "Unknown Date"))
    file_content = file_content.replace("BCK_IN_Mengen Kommentare", "Default Comment")
    file_content = file_content.replace("BCK_Organizations Name", "BCK Architecture")
    file_content = file_content.replace("BCK_Project Name", project.project_name)
    file_content = file_content.replace("BCK_Project Number", project.project_no)
    file_content = file_content.replace("BCK_Organization Description", "Architectural Firm")

    # Define file path
    file_path = f"media/projects/{project.project_no}_{project.project_name}_shared_params.txt"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    return file_path
