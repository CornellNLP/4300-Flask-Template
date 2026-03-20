import pandas as pd

class Rating:
    def __init__(self, date, rating, sentiment):
        self.date = date
        self.rating = rating
        #sent anal pos, negative, neutral. make an ENUM
        self.sentiment = sentiment


class Comment:
   def __init__(self, user, text, sentiment, rating=None, score=None, timestamp=None, controversiality=None):
        self.user = user
        self.text = text
        self.sentiment = sentiment
        self.rating = rating
        self.score = score
        self.timestamp = timestamp
        self.controversiality = controversiality

        # comment 
# id,timestamp,score,controversiality,text
comments_df = pd.read_csv("comments.csv")
comments_df = comments_df.set_index("id")

#uses character name to create the rating over time using character name
def get_rating_over_time(charName):

#creates comment object using comment id, will most likely be used in a loop iterating through reverse postings
def get_comment(id):
    com_csv = "data/piratefolk_comments.csv"
    #dummy data for now
    user = 'Pirate_Man22'
    text = comments_df
    TODO




class Character:
    def __init__(self, name, rank,total_comments, sentiment, sentiment_score, summary,
                 ratings_over_time=None, comments=None, retrieved=None):
        self.name = name
        #some trivial pattern matching function
        self.rank = rank
        #the sentiment that has the most in ratings over time
        self.sentiment = sentiment
        #make some metric using the enum
        self.sentiment_score = sentiment_score
        #ong put dummy data here for now
        self.summary = summary
        #complete ratings_over_time function
        self.ratings_over_time = ratings_over_time if ratings_over_time is not None else []
        #should be rating of final rating in ratings over time
        self.current_rating = self.ratings_over_time[len(ratings_over_time)]
        self.comments = comments if comments is not None else []
        self.total_comments = len(comments)
        #ask gabby what the difference was supposed to be... might be the ranked most relevant comments?
        self.retrieved = comments if comments is not None else[]



