# save_state_to_file.py
import os
import json
from datetime import datetime
import csv
import random

os.environ["GEMINI_API_KEY"] = "your_gemini_api_key"
os.environ["REASONING_MODEL"] = "gemini-2.0-flash"
os.environ["QUERY_GENERATOR_MODEL"] = "gemini-2.0-flash"
os.environ["REFLECTION_MODEL"] = "gemini-2.0-flash"
os.environ["ANSWER_MODEL"] = "gemini-2.0-flash"

def save_state_to_txt(state, filename=None):
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("GEMINI AGENT STATE REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # get final answer
        f.write("CONVERSATION\n")
        f.write("-" * 40 + "\n")
        if 'messages' in state:
            for i, msg in enumerate(state['messages']):
                if hasattr(msg, 'type'):
                    msg_type = msg.type.upper()
                    content = msg.content
                elif isinstance(msg, dict):
                    msg_type = msg.get('role', 'UNKNOWN').upper()
                    content = msg.get('content', str(msg))
                else:
                    msg_type = "UNKNOWN"
                    content = str(msg)
                
                f.write(f"\n[{msg_type}]: {content}\n")
        f.write("\n")
        
        # search statistics
        f.write("SEARCH STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Research loops completed: {state.get('research_loop_count', 0)}\n")
        f.write(f"Total search queries: {len(state.get('search_query', []))}\n")
        f.write(f"Sources gathered: {len(state.get('sources_gathered', []))}\n")
        f.write(f"Web research results: {len(state.get('web_research_result', []))}\n\n")
        
        # search queries used
        f.write("SEARCH QUERIES USED\n")
        f.write("-" * 40 + "\n")
        if 'search_query' in state:
            for i, query in enumerate(state['search_query'], 1):
                f.write(f"{i}. {query}\n")
        f.write("\n")
        
        # web search results
        f.write("WEB RESEARCH RESULTS\n")
        f.write("-" * 40 + "\n")
        if 'web_research_result' in state:
            for i, result in enumerate(state['web_research_result'], 1):
                f.write(f"\n--- Research Result {i} ---\n")
                f.write(f"{result}\n")
        f.write("\n")
        
        # sources gathered
        f.write("SOURCES GATHERED\n")
        f.write("-" * 40 + "\n")
        if 'sources_gathered' in state:
            for i, source in enumerate(state['sources_gathered'], 1):
                if isinstance(source, dict):
                    label = source.get('label', 'Unknown')
                    url = source.get('value', source.get('short_url', 'No URL'))
                    f.write(f"{i}. {label}\n   URL: {url}\n\n")
                else:
                    f.write(f"{i}. {source}\n\n")
        
        # raw state data
        f.write("RAW STATE DATA\n")
        f.write("-" * 40 + "\n")
        f.write("(Complete state in JSON format for debugging)\n\n")
        
        serializable_state = {}
        for key, value in state.items():
            try:
                if hasattr(value, '__dict__'):
                    serializable_state[key] = {
                        'type': str(type(value)),
                        'content': getattr(value, 'content', str(value))
                    }
                elif isinstance(value, list):
                    serializable_list = []
                    for item in value:
                        if hasattr(item, '__dict__'):
                            serializable_list.append({
                                'type': str(type(item)),
                                'content': getattr(item, 'content', str(item))
                            })
                        else:
                            serializable_list.append(item)
                    serializable_state[key] = serializable_list
                else:
                    serializable_state[key] = value
            except Exception as e:
                serializable_state[key] = f"Error serializing: {str(e)}"
        
        f.write(json.dumps(serializable_state, indent=2, ensure_ascii=False))
        
    print(f"State saved to: {filename}")
    return filename

def run_agent_and_save_state(question, q_id):

    print("Starting agent...")
    
    try:
        from agent import graph
        
        state = graph.invoke({
            "messages": [{"role": "user", 
                          "content": question}],
            "max_research_loops": 3,
            "initial_search_query_count": 3
        })
        
        print("Agent completed successfully!")
        
        filename = save_state_to_txt(state, f'states_resuquestion_{q_id}_state.txt')
        print(f"\nFinal Answer Preview:")
        print("-" * 40)
        if 'messages' in state and state['messages']:
            final_message = state['messages'][-1]
            if hasattr(final_message, 'content'):
                print(final_message.content[:300] + "...")
            else:
                print(str(final_message)[:300] + "...")
        
        print(f"\nQuick Stats:")
        print(f"   Research loops: {state.get('research_loop_count', 0)}")
        print(f"   Search queries: {len(state.get('search_query', []))}")
        print(f"   Sources found: {len(state.get('sources_gathered', []))}")
        
        return filename
        
    except Exception as e:
        print(f"Agent failed: {e}")

        error_state = {
            "error": str(e),
            "error_type": str(type(e)),
            "timestamp": datetime.now().isoformat()
        }
        filename = save_state_to_txt(error_state, "agent_error_state.txt")
        return filename

if __name__ == "__main__":
    csv_file = "questions_set.csv"  

    # Read questions
    questions = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                questions.append((row[0], row[1]))  # (id, question)

    # Randomly select 10 questions
    selected = random.sample(questions, min(10, len(questions)))

    for question_id, question in selected:    
        run_agent_and_save_state(question, question_id)