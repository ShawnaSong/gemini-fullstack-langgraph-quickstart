import json
import os
import glob
from collections import defaultdict
import re

def load_usage_data(file_path):
    """Load usage data from JSON array format"""
    usage_records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                usage_records = data
            else:
                usage_records = [data]
    except FileNotFoundError:
        print(f"Usage file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []
    
    print(f"Loaded {len(usage_records)} usage records")
    return usage_records

def load_question_data(directory):
    """Load question data from JSON files"""
    question_data = {}
    json_files = glob.glob(os.path.join(directory, "state_result_*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract question ID from filename
            filename = os.path.basename(file_path)
            question_id_match = re.search(r'state_result_(\d+)\.json', filename)
            if question_id_match:
                question_id = int(question_id_match.group(1))
                
                # Extract human and AI messages
                human_message = ""
                ai_message = ""
                
                if 'data' in data and 'messages' in data['data']:
                    messages = data['data']['messages']
                    for msg in messages:
                        if msg.get('type') == 'human':
                            human_message = msg.get('content', '')
                        elif msg.get('type') == 'ai':
                            ai_message = msg.get('content', '')
                search_queries = data.get('data', {}).get('search_query', [])
                
                question_data[question_id] = {
                    'question_id': question_id,
                    'filename': filename,
                    'human_message': human_message,
                    'ai_message': ai_message,
                    'search_queries': search_queries,
                    'web_research_results': [],
                    'web_search_usage': [] 
                }
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(question_data)} question files")
    return question_data

def extract_web_search_data(usage_records, question_data):
    """
    遍历usage记录，找到state为web_search的数据，
    根据search_queries的内容匹配对应的web_research_results，
    记录每个web_search的input_tokens和output_tokens
    """
    # 按question分组usage记录
    question_usage_map = defaultdict(list)
    question_ids = sorted(question_data.keys())
    cur_idx = -1
    
    for record in usage_records:
        state = record.get('state', '')
        if state == 'generate_query':
            # 新一轮开始
            cur_idx += 1
        elif state == 'finalize_answer':
            # 当前轮结束
            pass
        elif state == 'web_research':
            # 记录web_search数据，确保cur_idx在有效范围内
            if 0 <= cur_idx < len(question_ids):
                qid = question_ids[cur_idx]
                usage = {
                    'input_tokens': record.get('input_tokens'),
                    'output_tokens': record.get('output_tokens'),
                    'prompt': record.get('prompt'),
                    'output': record.get('output')
                }
                question_usage_map[qid].append(usage)
    
    # 处理每个question的数据，根据search_queries匹配web_research_results
    for qid in question_usage_map:
        if qid in question_data:
            web_search_records = question_usage_map[qid]
            search_queries = question_data[qid]['search_queries']
            
            # 根据search_queries的顺序匹配对应的web_research_results
            matched_results = []
            matched_usage = []
            
            # 为每个search_query按顺序找到对应的web_research_result
            for query in search_queries:
                found_match = False
                # 在web_search_records中查找包含该query的prompt
                for record in web_search_records:
                    prompt = record.get('prompt', '')
                    # 检查query是否在prompt中（不区分大小写）
                    if query.lower() in prompt.lower():
                        matched_results.append(record)
                        matched_usage.append({
                            'input_tokens': record['input_tokens'],
                            'output_tokens': record['output_tokens'],
                            'prompt': record['prompt'],
                            'output': record['output']
                        })
                        found_match = True
                        break  # 找到匹配的就跳出内层循环
                
                # 如果没有找到匹配的，添加空记录以保持索引一致
                if not found_match:
                    matched_results.append({})
                    matched_usage.append({
                        'input_tokens': None,
                        'output_tokens': None,
                        'prompt': None,
                        'output': None
                    })
            
            question_data[qid]['web_research_results'] = matched_results
            question_data[qid]['web_search_usage'] = matched_usage
    
    return question_data

def create_output_format(question_data):
    """Create output in the same format as collected_data.json"""
    
    # Count statistics
    total_questions = len(question_data)
    total_web_search_records = sum(len(q.get('web_research_results', [])) for q in question_data.values())
    total_web_search_tokens = sum(len(q.get('web_search_usage', [])) for q in question_data.values())
    
    # Create summary
    summary = {
        "total_questions": total_questions,
        "total_web_search_records": total_web_search_records,
        "total_web_search_tokens": total_web_search_tokens
    }
    
    # Create questions list
    questions = []
    for question_id in sorted(question_data.keys()):
        question_info = question_data[question_id]
        questions.append({
            "question_id": question_info['question_id'],
            "filename": question_info['filename'],
            "human_message": question_info['human_message'],
            "ai_message": question_info['ai_message'],
            "search_queries": question_info['search_queries'],
            # "web_research_results": question_info['web_research_results'],
            "web_search_usage": question_info['web_search_usage']
        })
    
    return {
        "summary": summary,
        "questions": questions
    }

def main():
    # File paths
    usage_file = "new_usage.json"
    output_dir = "new_output_json"
    output_file = "new_collected_data.json"
    
    print("Loading usage data...")
    usage_records = load_usage_data(usage_file)
    
    print("Loading question data...")
    question_data = load_question_data(output_dir)
    
    print("Extracting web search data...")
    # print(usage_records[0])
    question_data = extract_web_search_data(usage_records, question_data)
    
    print("Creating output format...")
    output_data = create_output_format(question_data)
    
    print("Saving output...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Output saved to {output_file}")
    print(f"Summary: {output_data['summary']}")

if __name__ == "__main__":
    main()

