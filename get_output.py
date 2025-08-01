import os
import json
from datetime import datetime
import csv
import random
import time

# Use valid model names that are available
os.environ["REASONING_MODEL"] = "gemini-2.0-flash"
os.environ["QUERY_GENERATOR_MODEL"] = "gemini-2.0-flash"
os.environ["REFLECTION_MODEL"] = "gemini-2.0-flash"
os.environ["ANSWER_MODEL"] = "gemini-2.0-flash"

from agent import graph
from langchain_core.messages import BaseMessage
import json

csv_file = "questions_set_new.csv"  
results_path = "new_output/"

# Read questions
questions = []
with open(csv_file, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        if len(row) >= 2:
            questions.append((row[0], row[1])) 

# for question_id, question in questions[325:400]:
#     print("question_id: ", question_id, "question: ", question, )

# question_id, question = questions[0]
# state = graph.invoke({
#             "messages": [{"role": "user", "content": question}],
#             "max_research_loops": 3,
#             "initial_search_query_count": 3
#         })

start_index = 793
end_index = 850
cur_index = start_index
for question_id, question in questions[start_index:end_index]:
    print("question_id: ", question_id, "start", "index: ", cur_index)
    state = graph.invoke({
                "messages": [{"role": "user", "content": question}],
                "max_research_loops": 3,
                "initial_search_query_count": 3
            })
    time.sleep(5)
    # with open(results_path + f"state_result_{question_id}.json", "w") as f:
    #     json.dump(state, f)
    with open(results_path + f"state_result_{question_id}.json", "w", encoding="utf-8") as f:
        f.write(str(state))
    print("question_id: ", question_id, "saved")
    cur_index += 1
