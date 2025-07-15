import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ProcessPoolExecutor

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set Tesseract and Poppler paths (modify as needed)
pytesseract.pytesseract.tesseract_cmd = r'D:\DAD PROJ\TESSERACT\tesseract.exe'
POPPLER_PATH = r'D:\DAD PROJ\poppler\poppler-24.08.0\Library\bin'


# ---------- OCR Helper Function for Multiprocessing ----------
def ocr_page(page_image_and_index, search_term):
    index, image = page_image_and_index
    text = pytesseract.image_to_string(image)
    if search_term.lower() in text.lower():
        return index + 1
    return None


# ---------- Main OCR Logic ----------
def find_word_in_pdf(pdf_path, search_term):
    images = convert_from_path(pdf_path, dpi=150, poppler_path=POPPLER_PATH)
    indexed_images = list(enumerate(images))

    found_pages = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(ocr_page, img, search_term) for img in indexed_images]
        for future in futures:
            result = future.result()
            if result is not None:
                found_pages.append(result)

    return sorted(found_pages)


# ---------- Flask Routes ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form['search_term']
        uploaded_file = request.files['file']

        if uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            # Run OCR to find word in parallel
            found_pages = find_word_in_pdf(filepath, search_term)

            return render_template('index.html', pages=found_pages, term=search_term)

    return render_template('index.html')


if __name__ == '__main__':
    # For multiprocessing to work on Windows
    import multiprocessing
    multiprocessing.freeze_support()

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
