import os
import json
import base64
import requests


def encode_image_to_base64(image_path):
    """
    Encode an image to a base64 string.

    :param image_path: Path to the image file.
    :return: Base64-encoded string of the image.
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {image_path}. Error: {e}")
        return None


def describe_with_curl(model, image_path=None, text=None):
    """
    Generate a description using the Ollama Vision API via curl-style requests.

    :param model: Name of the Ollama model (e.g., llama3.2-vision).
    :param image_path: Path to the image (for files that can be visualized).
    :param text: Fallback textual input (e.g., folder or file name).
    :return: Generated description or a default message.
    """
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": []
    }

    if image_path:
        # Encode the image to Base64
        image_data = encode_image_to_base64(image_path)
        if image_data:
            payload["messages"].append({
                "role": "user",
                "content": "What is in this image?",
                "images": [image_data]
            })
        else:
            return "Error encoding the image for description."
    else:
        # Use text-based description if no image is provided
        payload["messages"].append({
            "role": "user",
            "content": f"Describe this: {text}"
        })

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("content", "No description available")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error making the request: {e}"


def scan_folder(folder_path, model="llama3.2-vision"):
    """
    Recursively scans a folder and builds a JSON structure with descriptions.

    :param folder_path: The root folder to scan.
    :param model: The name of the Ollama model to use for descriptions.
    :return: JSON-like dict representing the folder structure.
    """
    result = {
        "name": os.path.basename(folder_path),
        "path": os.path.abspath(folder_path),
        "type": "folder",
        "description": describe_with_curl(model, text=os.path.basename(folder_path)),
        "children": []
    }

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            result["children"].append(scan_folder(item_path, model))
        else:
            description = describe_with_curl(
                model,
                image_path=item_path if item.lower().endswith(("png", "jpg", "jpeg", "gif")) else None,
                text=item
            )
            result["children"].append({
                "name": item,
                "path": os.path.abspath(item_path),
                "type": "file",
                "description": description
            })

    return result


def main():
    folder_path = input("Enter the path to the folder you want to scan: ").strip()
    model = "llama3.2-vision"

    if not os.path.exists(folder_path):
        print("The specified folder does not exist.")
        return

    print("Scanning folder and generating descriptions...")
    folder_structure = scan_folder(folder_path, model=model)

    output_file = os.path.join(folder_path, "folder_structure.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(folder_structure, f, indent=4)

    print(f"Folder structure saved to {output_file}")


if __name__ == "__main__":
    main()
