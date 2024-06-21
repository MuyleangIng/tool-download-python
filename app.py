from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify, request, send_file
import subprocess
import re
import os
import pandas as pd

from werkzeug.utils import secure_filename
app = Flask(__name__)
SWAGGER_URL = '/swagger'
API_URL = '/swagger.json'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}  # Allowed file extensions
app.config['UPLOAD_FOLDER'] = './uploads'  # Folder to store uploaded files

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Image Downloader API"
    }
)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/swagger.json')
def swagger_json():
    # Define your Swagger specification here
    swagger_spec = {
        "swagger": "2.0",
        "info": {
            "title": "Image Downloader API",
            "description": "API for downloading images from Google Drive links",
            "version": "1.0"
        },
        "paths": {
            "/download_images": {
                "get": {
                    "summary": "Download images from Google Drive links",
                    "responses": {
                        "200": {
                            "description": "List of downloaded images"
                        },
                        "400": {
                            "description": "Bad request, mismatch between links and names"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    }
                }
            },
            "/upload_convert": {
                "post": {
                    "summary": "Upload a file and convert it to CSV, extract 'English name' and 'Official follow store' columns",
                    "responses": {
                        "200": {
                            "description": "CSV file with extracted columns successfully created"
                        },
                        "400": {
                            "description": "Bad request or unsupported file format"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    },
                    "consumes": ["multipart/form-data"],
                    "parameters": [
                        {
                            "name": "file",
                            "in": "formData",
                            "description": "File to upload (CSV or XLSX)",
                            "required": True,
                            "type": "file"
                        }
                    ]
                }
            }
        }
    }
    return jsonify(swagger_spec)
@app.route('/upload_convert', methods=['POST'])
def upload_convert():
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['file']
        
        # If user does not select a file, browser also submits an empty part without filename
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Check if the file has an allowed extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the uploaded file
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                return jsonify({"error": "Unsupported file format. Please upload CSV or XLSX"}), 400
            
            # Ensure column names match exactly (case-sensitive)
            expected_columns = ['English Name', 'Official Photo']
            existing_columns = df.columns.tolist()
            
            for column in expected_columns:
                if column not in existing_columns:
                    return jsonify({"error": f"Column '{column}' not found in the uploaded file"}), 400
            
            # Select specific columns
            df_selected = df[expected_columns]
            
            # Save the selected data to a new CSV file
            processed_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_data.csv')
            df_selected.to_csv(processed_file_path, index=False)
            
            return send_file(processed_file_path, as_attachment=True, attachment_filename='processed_data.csv')
        
        else:
            return jsonify({"error": "Unsupported file format. Please upload CSV or XLSX"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/download_images', methods=['GET'])
def download_images():
    try:
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
            return jsonify({"error": "The number of links and names do not match!"}), 400

        downloads_info = []

        for link, name in zip(links, names):
            sanitized_name = name.strip()
            sanitized_name = re.sub(r'\s+', '_', sanitized_name)  # Replace spaces with underscores
            sanitized_name = re.sub(r'[^\w\-_\.]', '', sanitized_name)  # Remove special characters
            sanitized_name = sanitized_name.upper()  # Convert to uppercase

            # Extract the file ID from the Google Drive link
            file_id = re.search(r'id=([\w\-_]+)', link).group(1)
            download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

            # Prepare the wget command
            cmd = f"wget --no-check-certificate '{download_link}' -O '{os.path.join(download_dir, sanitized_name)}.png'"

            # Execute the wget command
            try:
                subprocess.run(cmd, check=True, shell=True)
                downloads_info.append({"name": sanitized_name, "status": "success"})
            except subprocess.CalledProcessError as e:
                downloads_info.append({"name": sanitized_name, "status": "failed", "error": str(e)})

        return jsonify({"downloads": downloads_info}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
