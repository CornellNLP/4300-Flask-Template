
class Rating:
    def __init__(self, date, rating):
        self.date = date
        self.rating = rating

class Comment:
   def __init__(self, user, text, sentiment, rating=None, score=None, timestamp=None, controversiality=None):
        self.user = user
        self.text = text
        self.sentiment = sentiment
        self.rating = rating
        self.score = score
        self.timestamp = timestamp
        self.controversiality = controversiality

class Character:
    def __init__(self, name, rank, current_rating, total_comments, sentiment, sentiment_score, summary,
                 ratings_over_time=None, comments=None, retrieved=None):
        self.name = name
        self.rank = rank
        self.current_rating = current_rating
        self.total_comments = total_comments
        self.sentiment = sentiment
        self.sentiment_score = sentiment_score
        self.summary = summary
        self.ratings_over_time = ratings_over_time if ratings_over_time is not None else []
        self.comments = comments if comments is not None else []
        self.retrieved = retrieved if retrieved is not None else []