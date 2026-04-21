# College AI Chatbot

A comprehensive web-based AI Chatbot designed to handle college administration queries such as admissions, library info, and deadlines. It leverages natural language processing (NLTK/spaCy), TF-IDF, and a Logistic Regression classifier to determine intents from user queries. Built with Flask for the backend, SQLAlchemy for database tracking, and a modern glassmorphic interface on the frontend.

## Features
- Natural language classification models
- Interactive dark-theme UI with CSS Animations and Scroll Reveal
- Custom mouse cursor and dynamic 3D tilt effects
- Local session-based message tracking
- Dedicated Administrator Dashboard for analytics and usage statistics

## Architecture
- **Backend:** Flask, Python
- **Database:** SQLite (via SQLAlchemy)
- **Machine Learning:** Scikit-Learn, NLTK, spaCy
- **Frontend:** HTML/CSS/JS, Chart.js, Tailwind-like custom styling

## Setup Instructions

1. **Clone the Repository**

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate       # On Mac/Linux
   venv\Scripts\activate          # On Windows
   ```

3. **Install Dependencies**
   Ensure you have all the required Python modules.
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If `nlp_engine.py` uses spaCy models, you may need to download the language dataset `python -m spacy download en_core_web_sm`.*

4. **Train the Model**
   Run the model script to generate your model assets from the `intents.json`.
   ```bash
   python train_model.py
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   Your server will start and you can access:
   - Chat interface: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - Admin Dashboard: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
