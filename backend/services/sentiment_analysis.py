# backend/services/sentiment_analysis.py
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

BERT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL)
model = AutoModelForSequenceClassification.from_pretrained(BERT_MODEL)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    return_all_scores=True
)

def analyze_sentiment(text: str):
    result = sentiment_pipeline(text)[0]
    return max(result, key=lambda x: x['score'])