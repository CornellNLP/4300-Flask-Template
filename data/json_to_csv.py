import json
import os
from pathlib import Path


with open("data_set.csv", "w") as f:
    directory_path = Path('./data/comments_data')
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            print(file_path.name)
            # You can also read the file content directly
            content = file_path.read_text()
            json_content = json.loads(content)
            for i in range(100):
                try:
                    json_content['data'][i]
                except KeyError:
                    continue
                comment_id = json_content['data'][i]['id']
                comment_text = json_content['data'][i]['body']
                cleaned_comment_text = comment_text.replace('\n', ' ').replace('\r', ' ').replace('"', '')
                comment_timestamp = json_content['data'][i]['created_utc']

                f.write(f'{comment_id},{comment_timestamp},\"{cleaned_comment_text}\"\n')
    
    

    
