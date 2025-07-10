import json
import os
import glob
from typing import Dict, List, Any
import re

def count_tokens_approx(text: str) -> int:
    """Approximate token count using word count"""
    if not text:
        return 0
    # Simple word splitting by space
    words = text.split()
    return len(words)

def parse_usage_json(usage_file_path: str) -> List[Dict[str, Any]]:
    """Parse usage.json file and extract all usage records"""
    usage_records = []
    
    try:
        with open(usage_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Remove brackets at beginning and end, then split by comma
            content = content.strip()
            if content.startswith('['):
                content = content[1:]
            if content.endswith(']'):
                content = content[:-1]
            
            # Split each JSON object
            json_objects = content.split(',\n')
            
            for json_str in json_objects:
                json_str = json_str.strip()
                if json_str:
                    try:
                        record = json.loads(json_str)
                        usage_records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON record: {e}")
                        print(f"Problematic record: {json_str}")
                        continue
    except Exception as e:
        print(f"Error reading usage.json file: {e}")
    
    return usage_records

def extract_question_data(json_file_path: str) -> Dict[str, Any]:
    """Extract question data from a single JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract question number from filename
        filename = os.path.basename(json_file_path)
        question_number = re.search(r'state_result_(\d+)\.json', filename)
        question_id = int(question_number.group(1)) if question_number else None
        
        # Extract data
        result = {
            'question_id': question_id,
            'filename': filename,
            'messages': [],
            'search_queries': [],
            'web_research_results': []
        }
        
        if 'data' in data:
            data_content = data['data']
            
            # Extract messages
            if 'messages' in data_content:
                for msg in data_content['messages']:
                    if msg.get('type') == 'human':
                        result['messages'].append({
                            'type': 'human',
                            'content': msg.get('content', '')
                        })
                    elif msg.get('type') == 'ai':
                        result['messages'].append({
                            'type': 'ai',
                            'content': msg.get('content', '')
                        })
            
            # Extract search_query
            if 'search_query' in data_content:
                result['search_queries'] = data_content['search_query']
            
            # Extract web_research_result
            if 'web_research_result' in data_content:
                result['web_research_results'] = data_content['web_research_result']
        
        return result
    
    except Exception as e:
        print(f"Error processing file {json_file_path}: {e}")
        return None

def match_usage_with_questions(usage_records: List[Dict], question_data: List[Dict]) -> Dict[int, List[Dict]]:
    """Match usage records with question data, grouped by question ID"""
    # Sort usage records by timestamp
    sorted_usage = sorted(usage_records, key=lambda x: x.get('timestamp', 0))
    
    # Group by question ID
    question_usage_map = {}
    
    # Initialize empty list for each question ID
    for question in question_data:
        question_usage_map[question['question_id']] = []
    
    # Analyze usage records to detect question boundaries
    current_question_index = 0
    in_question = False
    current_question_usage = []
    
    for usage_record in sorted_usage:
        state = usage_record.get('state', '')
        
        # Detect start of new question (generate_query)
        if state == 'generate_query':
            # If already processing a question, save data from previous question
            if in_question and current_question_index < len(question_data):
                question_id = question_data[current_question_index]['question_id']
                if question_id not in question_usage_map:
                    question_usage_map[question_id] = []
                # Only add web_search records
                for record in current_question_usage:
                    if record.get('state') == 'web_search':
                        question_usage_map[question_id].append(record)
            
            # Start new question
            in_question = True
            current_question_usage = [usage_record]
            current_question_index += 1
        
        # Detect end of question (finalize_answer)
        elif state == 'finalize_answer':
            if in_question:
                current_question_usage.append(usage_record)
                
                # Save current question data
                if current_question_index <= len(question_data):
                    question_id = question_data[current_question_index - 1]['question_id']
                    if question_id not in question_usage_map:
                        question_usage_map[question_id] = []
                    # Only add web_search records
                    for record in current_question_usage:
                        if record.get('state') == 'web_search':
                            question_usage_map[question_id].append(record)
            
            # End current question
            in_question = False
            current_question_usage = []
        
        # Other states (web_search, reflection)
        elif in_question:
            current_question_usage.append(usage_record)
    
    return question_usage_map

def sort_queries_by_loops(question_data: List[Dict]) -> List[Dict]:
    """Group by loops and sort search_queries"""
    for question in question_data:
        queries = question['search_queries']
        results = question['web_research_results']
        
        if not queries or not results or len(queries) != len(results):
            continue
        
        # Analyze usage records to determine loop boundaries
        # Simplified processing here, assuming fixed number of loops per question
        # In practice, need to determine based on usage records
        
        # Assume same number of queries per loop
        # Need to adjust based on actual data
        total_queries = len(queries)
        
        # Simple assumption: if 5 queries, first 3 are first loop, last 2 are second loop
        # In practice, need to determine based on reflection state
        if total_queries >= 3:
            # First loop: first 3
            loop1_queries = queries[:3]
            loop1_results = results[:3]
            
            # Second loop: remaining
            loop2_queries = queries[3:]
            loop2_results = results[3:]
            
            # Sort queries by token count within each loop
            # Loop 1
            if loop1_queries:
                sorted_loop1 = sorted(
                    enumerate(loop1_queries), 
                    key=lambda x: count_tokens_approx(x[1])
                )
                sorted_loop1_queries = [item[1] for item in sorted_loop1]
                sorted_loop1_indices = [item[0] for item in sorted_loop1]
                sorted_loop1_results = [loop1_results[i] for i in sorted_loop1_indices]
            
            # Loop 2
            if loop2_queries:
                sorted_loop2 = sorted(
                    enumerate(loop2_queries), 
                    key=lambda x: count_tokens_approx(x[1])
                )
                sorted_loop2_queries = [item[1] for item in sorted_loop2]
                sorted_loop2_indices = [item[0] for item in sorted_loop2]
                sorted_loop2_results = [loop2_results[i] for i in sorted_loop2_indices]
            
            # Recombine: arrange by loop order
            final_queries = []
            final_results = []
            
            if loop1_queries:
                final_queries.extend(sorted_loop1_queries)
                final_results.extend(sorted_loop1_results)
            
            if loop2_queries:
                final_queries.extend(sorted_loop2_queries)
                final_results.extend(sorted_loop2_results)
            
            question['search_queries'] = final_queries
            question['web_research_results'] = final_results
    
    return question_data

def main():
    """Main function"""
    # File paths
    usage_file_path = 'usage.json'
    output_dir = 'origin_output_json'
    output_file = 'collected_data_v2.json'
    
    print("Starting data collection...")
    
    # 1. Parse usage.json
    print("Parsing usage.json...")
    usage_records = parse_usage_json(usage_file_path)
    print(f"Found {len(usage_records)} usage records")
    
    # 2. Process all question files
    print("Processing question files...")
    json_files = glob.glob(os.path.join(output_dir, 'state_result_*.json'))
    json_files.sort(key=lambda x: int(re.search(r'state_result_(\d+)\.json', x).group(1)))
    
    question_data = []
    for json_file in json_files:
        data = extract_question_data(json_file)
        if data:
            question_data.append(data)
    
    print(f"Processed {len(question_data)} question files")
    
    # 3. Sort by loops
    print("Sorting by loops...")
    question_data = sort_queries_by_loops(question_data)
    
    # 4. Match data
    print("Matching usage data with question data...")
    question_usage_map = match_usage_with_questions(usage_records, question_data)
    
    # 5. Create final output
    final_output = {
        'summary': {
            'total_questions': len(question_data),
            'total_usage_records': len(usage_records),
            'web_search_records': len([r for r in usage_records if r.get('state') == 'web_search'])
        },
        'questions': []
    }
    
    # Create detailed records for each question
    for question in question_data:
        question_record = {
            'question_id': question['question_id'],
            'filename': question['filename'],
            'human_message': '',
            'ai_message': '',
            'search_queries': question['search_queries'],
            'web_research_results': question['web_research_results'],
            'web_search_usage': []
        }
        
        # Extract message content
        for msg in question['messages']:
            if msg['type'] == 'human':
                question_record['human_message'] = msg['content']
            elif msg['type'] == 'ai':
                question_record['ai_message'] = msg['content']
        
        # Add corresponding web_search usage data
        question_id = question['question_id']
        if question_id in question_usage_map:
            for usage_record in question_usage_map[question_id]:
                if usage_record.get('state') == 'web_search':
                    question_record['web_search_usage'].append({
                        'input_tokens': usage_record.get('input_tokens', 0),
                        'output_tokens': usage_record.get('output_tokens', 0),
                        'total_tokens': usage_record.get('total_tokens', 0),
                        'timestamp': usage_record.get('timestamp', 0)
                    })
        
        # Sort web_search_usage by input_tokens
        if question_record['web_search_usage']:
            question_record['web_search_usage'].sort(key=lambda x: x['input_tokens'])
        
        final_output['questions'].append(question_record)
    
    # 6. Save results
    print("Saving results...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print(f"Data collection completed! Results saved to {output_file}")
    
    # 7. Print statistics
    print("\nStatistics:")
    print(f"Total questions: {len(question_data)}")
    print(f"Total usage records: {len(usage_records)}")
    
    # Calculate web_search related statistics
    web_search_records = [r for r in usage_records if r.get('state') == 'web_search']
    total_web_search_tokens = sum(r.get('total_tokens', 0) for r in web_search_records)
    
    print(f"Web search records: {len(web_search_records)}")
    print(f"Total web search token usage: {total_web_search_tokens}")

if __name__ == "__main__":
    main() 