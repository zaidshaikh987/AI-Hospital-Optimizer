# AI-Hospital-Optimizer!
![Screenshot 2025-03-27 125927](https://github.com/user-attachments/assets/7d25f3e3-c0bd-4bc2-b872-90664db651da)
![Screenshot 2025-03-27 125942](https://github.com/user-attachments/assets/d692d403-01ae-4452-b3b6-730654ca44af)
# 🏥 AI-Driven Hospital Optimization System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-green)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)

An intelligent system for hospital ranking, doctor matching, and patient flow optimization using AI/ML.

## ✨ Key Features

- **AI-Powered Hospital Ranking**  
  Dynamically ranks hospitals based on:
  - Real-time distance from patient
  - Bed availability & wait times
  - Historical success rates
  - Patient sentiment analysis

- **Smart Doctor Matching**  
  Recommends optimal doctors based on:
  - Symptom-specialization matching
  - Doctor experience & success rates
  - Hospital quality scores

- **Predictive Wait Times**  
  Forecasts patient wait times using:
  - Historical appointment data
  - Current queue lengths
  - Time-series forecasting (LSTM)

- **Sentiment Analysis**  
  Analyzes patient reviews with:
  - RoBERTa NLP model
  - Real-time feedback processing

## 🛠 Tech Stack

| Component       | Technology |
|-----------------|------------|
| Backend         | FastAPI (Python) |
| Frontend        | Streamlit |
| Geocoding       | Google Maps API |
| NLP             | HuggingFace Transformers |
| Data Storage    | JSON (Dummy Data) |
| Visualization   | PyDeck/Google Maps |

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Google Maps API Key (for geocoding)

### Installation
```bash
git clone https://github.com/yourusername/AI-Hospital-Optimizer.git
cd AI-Hospital-Optimizer/backend
pip install -r requirements.txt
