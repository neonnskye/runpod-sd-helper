import os
import re
import requests
import shutil
import zipfile
from typing import Union


def execute_user_choice(choice_values: Union[list, tuple], *target_functions):
    def display_invalid_input_error():
        print("Invalid input. Please enter a valid option.\n")

    print("\nPlease select an option")
    for i, choice in enumerate(choice_values):
        print(f"[{i+1}] {choice}")
    print()

    while True:
        try:
            choice = int(input("Enter your choice: "))
            if choice > len(choice_values) or choice < 1:
                display_invalid_input_error()
            else:
                break
        except ValueError:
            display_invalid_input_error()
    print()

    if len(target_functions) > 1:
        target_functions[choice - 1]()
    else:
        target_functions[0](choice_values[choice - 1])


def welcome():
    print("\nRunPod Stable Diffusion Helper by @neonnskye\n")
    print("IMPORTANT! MAKE SURE YOU ARE RUNNING FROM 'WORKSPACE' DIRECTORY")
    choice_names = ["Download models", "Edit datasets", "Transfer files", "Quit"]
    execute_user_choice(
        choice_names, download_models, edit_datasets, transfer_files, quit
    )


def download_models():
    print("Enter links to the models to be downloaded. Press Enter to finish.")
    print("(Example: https://civitai.com/models/43331/majicmix-realistic)\n")

    model_links = set()
    i = 1
    while True:
        model_link = input(f"Model {i}: ")
        if not model_link.strip():
            break
        elif re.findall(r"https:\/\/civitai\.com\/models\/\d+", model_link):
            model_links.add(model_link)
            i += 1
        else:
            print("Invalid link. Please enter a valid url.\n")

    print()

    [download_model(model_link) for model_link in model_links]

    print(f"\nFinished downloading {len(model_links)} models.")
    input("Press any key to continue: ")
    quit()


def get_model_metadata(model_url):
    match = re.search(r"models/(\d+)(?:\?modelVersionId=(\d+))?", model_url)

    if match:
        model_id = int(match.group(1))
        model_version_id = int(match.group(2)) if match.group(2) else None
    else:
        model_id = int(match.group(1))
        model_version_id = None

    response = requests.get(f"https://civitai.com/api/v1/models/{model_id}")
    json_data = response.json()

    model_name = json_data["name"]
    model_version_data = next(
        (data for data in json_data["modelVersions"] if data["id"] == model_version_id),
        json_data["modelVersions"][0],
    )
    model_version_file_data = model_version_data["files"][0]

    file_name = model_version_file_data["name"]
    download_url = model_version_file_data["downloadUrl"]
    model_type = json_data["type"]

    return model_name, file_name, download_url, model_type


def download_model(model_url):
    model_name, file_name, download_url, model_type = get_model_metadata(model_url)

    if model_type in ["Hypernetwork", "AestheticGradient", "Controlnet", "Poses"]:
        print(f"Skipped download '{model_name}': '{model_type}' is unsupported.")
        return

    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded_size = 0

    with open(file_name, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            downloaded_size += len(chunk)
            percentage = int((downloaded_size / total_size) * 100)
            print(f"Downloading '{model_name}': {percentage}% completed", end="\r")

    print()

    if model_type == "Checkpoint":
        destination_dir = "stable-diffusion-webui/models/Stable-diffusion/"
    elif model_type == "TextualInversion":
        destination_dir = "stable-diffusion-webui/embeddings/"
    elif model_type == "LORA":
        destination_dir = "stable-diffusion-webui/models/Lora/"

    shutil.move(file_name, os.path.join(destination_dir, file_name))


def edit_datasets():
    def verify_directory(directory):
        image_files = []
        text_files = []

        for file in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file)):
                if file.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp")
                ):
                    image_files.append(file)
                elif file.lower().endswith(".txt"):
                    text_files.append(file)

        if not image_files or not text_files:
            return False

        if len(image_files) != len(text_files):
            return False

        for image_file in image_files:
            image_name, _ = os.path.splitext(image_file)
            text_file = image_name + ".txt"
            if text_file not in text_files:
                return False

        return True

    dataset_directories = []
    for item_path in os.listdir():
        if os.path.isdir(item_path):
            if verify_directory(item_path):
                dataset_directories.append(item_path)

    print(f"Found {len(dataset_directories)} valid datasets! Select a dataset to edit.")
    execute_user_choice(dataset_directories, edit_dataset)


def edit_dataset(dataset_name):
    print("Uploading files...")
    upload_zip_filename = dataset_name + ".zip"
    with zipfile.ZipFile(upload_zip_filename, "w") as upload_zip_file:
        for item in os.listdir(dataset_name):
            upload_zip_file.write(os.path.join(dataset_name, item), item)

    url = "https://neonnskye.pythonanywhere.com/upload"

    with open(upload_zip_filename, "rb") as file:
        response = requests.post(url, files={"file": file})
        dataset_url = response.text.replace(" ", "%20")
    os.remove(upload_zip_filename)

    print("\nDataset uploaded successfully!")
    print(f"You can edit it at https://neonnskye.pythonanywhere.com/edit/{dataset_url}")
    input("\nPress any key to coninue after you submit your edits: ")

    print("\nDownloading...")
    response = requests.get(
        f"https://neonnskye.pythonanywhere.com/download/{dataset_url}", stream=True
    )
    download_zip_filename = dataset_name + ".zip"
    with open(download_zip_filename, "wb") as download_zip_file:
        for chunk in response.iter_content(chunk_size=8192):
            download_zip_file.write(chunk)

    with zipfile.ZipFile(download_zip_filename, "r") as zip_to_extract:
        zip_to_extract.extractall(dataset_name)
    os.remove(download_zip_filename)

    print("\nYour edits have been saved!")
    input("Press any key to continue: ")
    quit()


def transfer_files():
    print("transfer files")


if __name__ == "__main__":
    welcome()
