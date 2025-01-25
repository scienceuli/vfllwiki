from PIL import Image
import os

def resize_images_in_folder(folder_path, width=30):
    for filename in os.listdir(folder_path):
        if filename.startswith("button_") and filename.lower().endswith((".png", ".jpg", ".jpeg")):
            filepath = os.path.join(folder_path, filename)
            with Image.open(filepath) as img:
                aspect_ratio = img.height / img.width
                new_height = int(width * aspect_ratio)
                resized_img = img.resize((width, new_height))
                resized_img.save(filepath)  # Overwrite the original image
                print(f"Resized: {filename}")

if __name__ == "__main__":
    folder_path = "attachments"
    resize_images_in_folder(folder_path)
