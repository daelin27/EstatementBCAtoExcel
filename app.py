from flask import Flask, request, render_template, send_from_directory
import os
import estatement  # This should be the actual name of your script file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Ensure upload and result folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Call your script function here
        result_path = estatement.process_pdf(file_path, app.config['RESULT_FOLDER'])
        
        if result_path:
            return send_from_directory(app.config['RESULT_FOLDER'], os.path.basename(result_path))
        else:
            return 'File processing failed', 500

if __name__ == '__main__':
    app.run(debug=True)
