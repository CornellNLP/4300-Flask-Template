from infosci_spark_client import LLMClient
import os

def rag_answer(user_query, character):
    comments = character.retrieved

    context = "\n".join([
        f"Sentiment: {c.sentiment} | {c.text}"
        for c in comments[:10]
    ])

    prompt = f"""
    Use ONLY the comments below to answer the question.

    Question: {user_query}

    Comments:
    {context}
    """

    client = LLMClient(api_key=os.getenv("SPARK_API_KEY"))

    messages = [
        {"role": "system", "content": "You answer questions using provided comments only."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat(messages)

    return response.get("content")

def generate_character_summary(character):
    comments = character.comments[:10]

    context = "\n".join([
        f"Sentiment: {c.sentiment} | {c.text}"
        for c in comments
    ])

    prompt = f"""
    Write a short summary of the character based on these comments.

    Focus on:
    - overall sentiment (positive/negative/mixed)
    - key reasons people feel that way

    Comments:
    {context}
    """

    client = LLMClient(api_key=os.
                       env("SPARK_API_KEY"))

    messages = [
        {"role": "system", "content": "You summarize community sentiment clearly and briefly."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat(messages)
    return response.get("content", "")