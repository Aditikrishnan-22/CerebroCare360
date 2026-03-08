import os
import uuid
from PIL import Image
from flask import current_app

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10MB
MIN_FILE_SIZE = 10 * 1024           # 10KB
MIN_DIM = 64
MAX_DIM = 4096

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_and_save(file):
    """
    Validates and saves an uploaded MRI image.
    Returns (filename, error_message)
    """
    if not file or file.filename == '':
        return None, 'No file selected.'

    if not allowed_file(file.filename):
        return None, 'Only JPG and PNG files are allowed.'

    contents = file.read()
    size = len(contents)

    if size > MAX_FILE_SIZE:
        return None, 'File too large. Maximum size is 10MB.'
    if size < MIN_FILE_SIZE:
        return None, 'File too small. Minimum size is 10KB.'

    file.seek(0)

    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
        img = img.convert('RGB')
    except Exception:
        return None, 'Invalid or corrupted image file.'

    w, h = img.size
    if w < MIN_DIM or h < MIN_DIM:
        return None, f'Image too small. Minimum dimensions are {MIN_DIM}x{MIN_DIM}px.'
    if w > MAX_DIM or h > MAX_DIM:
        return None, f'Image too large. Maximum dimensions are {MAX_DIM}x{MAX_DIM}px.'

    filename = f"{uuid.uuid4().hex}.jpg"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    img.save(save_path, 'JPEG', quality=95)

    return filename, None