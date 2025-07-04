import os
import json
from datetime import datetime
import csv
import random

# Use valid model names that are available
os.environ["REASONING_MODEL"] = "gemini-2.0-flash-exp"
os.environ["QUERY_GENERATOR_MODEL"] = "gemini-2.0-flash-exp"
os.environ["REFLECTION_MODEL"] = "gemini-2.0-flash-exp"
os.environ["ANSWER_MODEL"] = "gemini-2.0-flash-exp"

from agent import graph
from langchain_core.messages import BaseMessage
import json

csv_file = "questions_set.csv"  
results_path = "origin_output/"

# Read questions
questions = []
with open(csv_file, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) >= 2:
            questions.append((row[0], row[1])) 

# question_id, question = questions[0]
# state = graph.invoke({
#             "messages": [{"role": "user", "content": question}],
#             "max_research_loops": 3,
#             "initial_search_query_count": 3
#         })
for question_id, question in questions[4:]:
    print("question_id: ", question_id, "start")
    state = graph.invoke({
                "messages": [{"role": "user", "content": question}],
                "max_research_loops": 3,
                "initial_search_query_count": 3
            })
    # with open(results_path + f"state_result_{question_id}.json", "w") as f:
    #     json.dump(state, f)
    with open(results_path + f"state_result_{question_id}.json", "w", encoding="utf-8") as f:
        f.write(str(state))
    print("question_id: ", question_id, "saved")
