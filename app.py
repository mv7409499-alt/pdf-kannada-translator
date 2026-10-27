
import os
import io
import fitz
from flask import Flask, request, render_template_string, send_file
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

LANGUAGES = {
    "Kannada": "kn",
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Bengali": "bn",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Arabic": "ar",
    "Japanese": "ja",
    "Chinese": "zh-CN"
}

PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PDF Translator</title>
<style>
body{font-family:Arial;background:#f0f4f8;margin:0;padding:20px}
main{max-width:600px;margin:35px auto;background:white;padding:24px;
border-radius:16px;box-shadow:0 4px 18px #0001}
h1{text-align:center;color:#185abd}
p{color:#444;line-height:1.5}
label{display:block;margin-top:18px;font-weight:bold}
input,select,button{box-sizing:border-box;width:100%;padding:13px;
margin-top:8px;border:1px solid #ccc;border-radius:8px;font-size:16px}
button{background:#185abd;color:white;border:0;font-weight:bold;margin-top:22px}
.note{font-size:13px;color:#666}
</style>
</head>
<body>
<main>
<h1>📄 PDF Translator</h1>
<p>Upload your PDF and translate its text into another language.</p>
<form method="POST" action="/translate" enctype="multipart/form-data">
<label>Select PDF file</label>
<input type="file" name="pdf" accept=".pdf,application/pdf" required>
<label>Translate into</label>
<select name="language">
{% for name, code in languages.items() %}
<option value="{{ code }}" {% if code == 'kn' %}selected{% endif %}>{{ name }}</option>
{% endfor %}
</select>
<button type="submit">Translate PDF</button>
</form>
<p class="note">Maximum file size: 15 MB. Scanned PDFs may need OCR.
Internet connection is required for translation.</p>
</main>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(PAGE, languages=LANGUAGES)

@app.route("/translate", methods=["POST"])
def translate():
    uploaded = request.files.get("pdf")
    target = request.form.get("language", "kn")

    if not uploaded or not uploaded.filename.lower().endswith(".pdf"):
        return "Please upload a PDF file.", 400

    if target not in LANGUAGES.values():
        return "Invalid target language.", 400

    try:
        data = uploaded.read()
        doc = fitz.open(stream=data, filetype="pdf")
        output = fitz.open()
        translated_any = False

        for page in doc:
            text = page.get_text("text").strip()
            if not text:
                continue

            translated = GoogleTranslator(
                source="auto", target=target
            ).translate(text)

            if translated:
                new_page = output.new_page(width=595, height=842)
                new_page.insert_textbox(
                    fitz.Rect(40, 40, 555, 800),
                    translated,
                    fontsize=11,
                    fontname="helv"
                )
                translated_any = True

        doc.close()

        if not translated_any:
            output.close()
            return ("No readable text found. Scanned PDFs need OCR first."), 400

        result = output.tobytes()
        output.close()

        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="translated.pdf"
        )

    except Exception as error:
        app.logger.exception("PDF translation failed")
        return (
            "Translation failed. Check your internet connection "
            "or try a smaller PDF. Details: " + str(error)
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
