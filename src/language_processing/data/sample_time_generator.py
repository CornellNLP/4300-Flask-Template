import requests
import os

# script for retrieving a bunch of json files of comments from the piratefolk subreddit

# stores in batches of 100 comments, one file for each week, in new folder "comments_data"

# uses pushpull.io api


current_unix_timestamp = 1773256079 # for Mar 11, 2026
day = 24 * 60 * 60
week = 7 * day
year = 365 * day


# end_timestap is the later time, and start_timestamp is the earlier time.
def list_timestamps(start_timestamp, end_timestamp, interval_seconds):
    timestamps = []
    current_timestamp = start_timestamp
    while current_timestamp <= end_timestamp:
        timestamps.append(current_timestamp)
        current_timestamp += interval_seconds
    return timestamps



def get_jsons(list_timestamps):
    if len(list_timestamps) == 0:
        return
    elif len(list_timestamps) > 1000:
        print("Too many timestamps.")
        return
    print(list_timestamps)

    os.mkdir("comments_data")
    for timestamp in list_timestamps:
        link = f"https://api.pullpush.io/reddit/search/comment/?subreddit=piratefolk&size=100&before={timestamp}"
        link_content = requests.get(link).content
        json = open(f'comments_data/data_{timestamp}.json', 'wb').write(link_content)
    
    return



start = current_unix_timestamp - (3 * year)
end = current_unix_timestamp
get_jsons(list_timestamps(start, end, week))


