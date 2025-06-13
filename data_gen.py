# extract_questions_v2.py
from datasets import load_dataset
import json
import random
from datetime import datetime
import csv

def extract_user_questions_from_dataset(num_questions=10, save_to_file=True):
    ds = load_dataset("lmarena-ai/search-arena-v1-7k")
    train_ds = ds['train'].select(range(num_questions))
    questions = []

    for i, sample in enumerate(train_ds):
        messages_a = sample.get('messages_a', [])
        print("messages_a: ", messages_a)
        if isinstance(messages_a, list) and len(messages_a) > 0:
            for msg in messages_a:
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    user_question = msg.get('content', '').strip()
                    if user_question and len(user_question) > 5:
                        questions.append({
                            'id': i,
                            'question': user_question,
                        })
                    break 

    with open("questions_set.csv", 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'question']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)   
        writer.writeheader()
        for question_data in questions:
            writer.writerow(question_data)
    return

if __name__ == "__main__":
    extract_user_questions_from_dataset(num_questions=100)