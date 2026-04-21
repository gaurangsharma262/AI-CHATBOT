"""
train_model.py — Model Training Script
======================================
Trains a TF-IDF + Logistic Regression intent classifier
on the intents.json dataset and saves the model as a .pkl file.

Run:  python train_model.py

Team Module: ML Engineer / Training
"""

import json
import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

from nlp_engine import preprocess

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, 'intents.json')
MODEL_PATH   = os.path.join(BASE_DIR, 'model', 'chatbot_model.pkl')
LABELS_PATH  = os.path.join(BASE_DIR, 'model', 'label_map.pkl')


def load_intents(path: str):
    """Load intents.json and return (texts, labels) lists."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts, labels = [], []
    for intent in data['intents']:
        tag = intent['tag']
        for pattern in intent['patterns']:
            preprocessed = preprocess(pattern)
            texts.append(preprocessed)
            labels.append(tag)

    return texts, labels


def build_pipeline() -> Pipeline:
    """
    Build sklearn Pipeline:
      TF-IDF Vectorizer → Logistic Regression classifier

    TF-IDF settings:
      - ngram_range (1,2): unigrams + bigrams for richer features
      - max_features 5000: cap vocabulary size
      - sublinear_tf True: log-scaled term frequency

    Logistic Regression:
      - C=10: regularization strength
      - max_iter=500: ensure convergence
      - solver='lbfgs': efficient for multi-class
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            analyzer='word'
        )),
        ('clf', LogisticRegression(
            C=10,
            max_iter=500,
            solver='lbfgs'
        ))
    ])
    return pipeline


def train():
    """Main training routine."""
    print("=" * 55)
    print("  NeuralChat — Intent Classifier Training")
    print("=" * 55)

    # 1. Load & preprocess data
    print("\n[1/4] Loading intents from intents.json...")
    texts, labels = load_intents(INTENTS_PATH)
    unique_labels = sorted(set(labels))
    print(f"      Loaded {len(texts)} training samples across {len(unique_labels)} intents.")
    print(f"      Intents: {unique_labels}")

    # 2. Train / test split
    print("\n[2/4] Splitting dataset (80% train / 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"      Train: {len(X_train)} | Test: {len(X_test)}")

    # 3. Train pipeline
    print("\n[3/4] Training TF-IDF + Logistic Regression pipeline...")
    model = build_pipeline()
    model.fit(X_train, y_train)

    # 4. Evaluate
    print("\n[4/4] Evaluating model...")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n  [OK] Test Accuracy: {acc * 100:.2f}%")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 5. Save model & label map
    os.makedirs(os.path.join(BASE_DIR, 'model'), exist_ok=True)

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)

    label_map = {i: label for i, label in enumerate(unique_labels)}
    with open(LABELS_PATH, 'wb') as f:
        pickle.dump(label_map, f)

    print(f"\n  Model saved  => {MODEL_PATH}")
    print(f"  Labels saved => {LABELS_PATH}")
    print("\n" + "=" * 55)
    print("  Training complete! Run app.py to start the server.")
    print("=" * 55)

    return model, acc


if __name__ == '__main__':
    train()
