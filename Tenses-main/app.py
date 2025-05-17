from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import spacy

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
# Enable CORS for your frontend origin
CORS(app, resources={r"/detect-tense": {"origins": "http://127.0.0.1:5500"}})

# Load spaCy model
nlp = spacy.load('en_core_web_sm')


def detect_tense(text):
    """
    Analyze the input text and return 'present', 'past', or 'future' based on majority tense detected.
    """
    doc = nlp(text)
    tenses = {"present": 0, "past": 0, "future": 0}
    
    has_future_modal = False
    has_base_or_gerund_after_modal = False
    
    for i, token in enumerate(doc):
        # Count verbs and auxiliaries
        if token.pos_ in ("VERB", "AUX"):
            # Present forms
            if token.tag_ in ["VBP", "VBZ", "VBG"]:
                tenses["present"] += 1
            # Past forms
            elif token.tag_ in ["VBD", "VBN"]:
                tenses["past"] += 1
            # Modal verbs (e.g. will/shall) for future
            elif token.tag_ == "MD" and token.text.lower() in ["will", "shall"]:
                has_future_modal = True
                # Lookahead for base form or gerund
                if i + 1 < len(doc) and doc[i+1].tag_ in ["VB", "VBG"]:
                    has_base_or_gerund_after_modal = True
        # "going to" future construction
        if token.text.lower() in ["is", "are", "am"] and i+2 < len(doc):
            if doc[i+1].text.lower() == "going" and doc[i+2].tag_ in ["VB", "VBG"]:
                tenses["future"] += 1

    if has_future_modal and has_base_or_gerund_after_modal:
        tenses["future"] += 1

    # Determine and return majority tense
    return max(tenses, key=tenses.get)


@app.route('/')
def home():
    """Render the main UI."""
    return render_template('index.html')


@app.route('/detect-tense', methods=['POST'])
def detect_tense_api():
    """API endpoint to detect tense of submitted text."""
    data = request.get_json() or {}
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    tense = detect_tense(text)
    return jsonify({"tense": tense})


if __name__ == '__main__':
    app.run(debug=True)
