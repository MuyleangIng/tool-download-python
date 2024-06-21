from flask import Flask, jsonify, request, send_file
import pandas as pd
from werkzeug.utils import secure_filename
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'  # Folder to store uploaded files
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}  # Allowed file extensions

SWAGGER_URL = '/swagger'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "File Upload and Conversion API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/swagger.json')
def swagger_json():
    # Define your Swagger specification here
    swagger_spec = {
        "swagger": "2.0",
        "info": {
            "title": "File Upload and Conversion API",
            "description": "API for uploading files and converting them to CSV format, extracting specific columns",
            "version": "1.0"
        },
        "paths": {
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
            
            # Extract specific columns
            selected_columns = ['English name', 'Official follow store']
            df_selected = df[selected_columns]
            
            # Save the selected data to a new CSV file
            processed_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_data.csv')
            df_selected.to_csv(processed_file_path, index=False)
            
            return send_file(processed_file_path, as_attachment=True, attachment_filename='processed_data.csv')
        
        else:
            return jsonify({"error": "Unsupported file format. Please upload CSV or XLSX"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
