

#load sentiment analyis model
#categorize as positive negative neutral
#sentiments are an enum of positive, negative, neutral
from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = sia.polarity_scores(text)["compound"]
    
    if score > 0.05:
        return "positive"
    elif score < -0.05:
        return "negative"
    else:
        return "neutral"

"""print(get_sentiment("I love this game!")) # positive
print(get_sentiment("This game is terrible.")) # negative
print(get_sentiment("This game is okay.")) # neutral"""
