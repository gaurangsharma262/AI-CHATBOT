"""
nlp_engine.py — NLP Preprocessing Pipeline
==========================================
Uses NLTK + spaCy for:
  - Tokenization
  - Stopword removal
  - Lemmatization
  - Text cleaning

Team Module: NLP Engineer
"""

import re
import string
import nltk
try:
    import spacy
except ImportError:
    spacy = None
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# ── Download required NLTK data (only first run) ──────────────────────────────
def download_nltk_data():
    resources = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'punkt_tab']
    for r in resources:
        try:
            nltk.download(r, quiet=True)
        except Exception:
            pass

download_nltk_data()

# ── Load spaCy English model ──────────────────────────────────────────────────
if spacy is not None:
    try:
        nlp_model = spacy.load("en_core_web_sm")
    except OSError:
        # If model not found, user must run: python -m spacy download en_core_web_sm
        nlp_model = None
        print("[WARNING] spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
else:
    nlp_model = None
    print("[WARNING] spaCy is not installed. Using NLTK fallback only.")

# ── NLTK stopwords ────────────────────────────────────────────────────────────
STOP_WORDS = set(stopwords.words('english'))

# Keep some question words that carry intent meaning
KEEP_WORDS = {'what', 'where', 'when', 'who', 'how', 'which', 'why'}
STOP_WORDS -= KEEP_WORDS


def clean_text(text: str) -> str:
    """
    Basic text cleaning:
    - Lowercase
    - Remove punctuation and special characters
    - Strip extra whitespace
    """
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)   # keep only alphanumeric + spaces
    text = re.sub(r'\s+', ' ', text)            # collapse multiple spaces
    return text


def tokenize_nltk(text: str) -> list:
    """Tokenize text using NLTK word_tokenize."""
    return word_tokenize(text)


def remove_stopwords(tokens: list) -> list:
    """Remove stopwords from token list."""
    return [t for t in tokens if t not in STOP_WORDS]


def lemmatize_spacy(text: str) -> str:
    """
    Lemmatize text using spaCy.
    Returns space-joined lemmas of content words.
    Falls back to NLTK-only if spaCy model unavailable.
    """
    if nlp_model is None:
        # Fallback: just return cleaned text
        return text

    doc = nlp_model(text)
    # Lemmatize, keep only alpha tokens that aren't stopwords
    lemmas = [
        token.lemma_
        for token in doc
        if token.is_alpha and not token.is_stop
    ]
    return ' '.join(lemmas)


def preprocess(text: str) -> str:
    """
    Full NLP preprocessing pipeline:
      1. Clean text
      2. Lemmatize with spaCy (removes stops internally)
      3. Fallback: NLTK tokenize + stopword removal
    
    Returns preprocessed string ready for TF-IDF vectorization.
    """
    cleaned = clean_text(text)

    if nlp_model is not None:
        # spaCy pipeline handles lemmatization + stop removal
        processed = lemmatize_spacy(cleaned)
        if not processed.strip():
            # If spaCy stripped everything (e.g. all stops), use fallback
            tokens = tokenize_nltk(cleaned)
            processed = ' '.join(tokens)
    else:
        # NLTK fallback pipeline
        tokens = tokenize_nltk(cleaned)
        tokens = remove_stopwords(tokens)
        processed = ' '.join(tokens)

    return processed if processed.strip() else cleaned
