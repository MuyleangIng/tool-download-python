import subprocess
import re
import os

# Load all links and names
with open('linkList.txt', 'r') as f:
    links = f.read().splitlines()

with open('nameList.txt', 'r') as f:
    names = f.read().splitlines()

# Create the downloads directory if it does not exist
download_dir = './downloads'
os.makedirs(download_dir, exist_ok=True)

# Check if the number of links and names match
if len(links) != len(names):
    print("The number of links and names do not match!")
else:
    for link, name in zip(links, names):
        try:
            # Sanitize the name for use as a filename
            sanitized_name = name.strip()
            sanitized_name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
            sanitized_name = re.sub(r'[^\w\-_\.]', '', sanitized_name)  # Remove special characters
            sanitized_name = sanitized_name.upper()  # Convert to uppercase

            # Extract the file ID from the Google Drive link
            file_id = re.search(r'id=([\w\-_]+)', link).group(1)
            download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

            # Prepare the wget command
            cmd = f"wget --no-check-certificate '{download_link}' -O '{os.path.join(download_dir, sanitized_name)}.png'"
            # Execute the wget command
            subprocess.run(cmd, check=True, shell=True)
            print(f"Downloaded and saved {sanitized_name} successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to download {link}: {str(e)}")