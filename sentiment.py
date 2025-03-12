from transformers import pipeline

classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def get_sentiment(transcript):
    return classifier(transcript)


if __name__ == "__main__":
    result = get_sentiment("I am so happy")
    print(result)
    