#!/usr/bin/env python3
"""
Simple script to convert existing output files to proper JSON format using eval
"""

import os
import json
from datetime import datetime

def convert_to_json_serializable(obj):
    """Convert complex objects to JSON serializable format"""
    if hasattr(obj, '__dict__'):
        # Convert objects to dict
        return obj.__dict__
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif hasattr(obj, 'content'):
        # Handle message objects
        return {
            'type': obj.__class__.__name__,
            'content': obj.content,
            'id': getattr(obj, 'id', None),
            'additional_kwargs': getattr(obj, 'additional_kwargs', {}),
            'response_metadata': getattr(obj, 'response_metadata', {})
        }
    else:
        return str(obj)

def convert_file_to_json(input_file, output_file):
    """Convert a single file to JSON format"""
    try:
        # Read the file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Use eval to parse the Python dictionary (safe in this context)
        # First, we need to import the message classes
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Evaluate the content
        data = eval(content)
        
        # Convert to JSON serializable format
        json_data = convert_to_json_serializable(data)
        
        # Add metadata
        output_data = {
            "file_name": os.path.basename(input_file),
            "conversion_timestamp": datetime.now().isoformat(),
            "data": json_data
        }
        
        # Save as JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Converted {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"Error converting {input_file}: {e}")
        return False

def convert_all_files():
    """Convert all files in origin_output directory"""
    input_dir = "origin_output"
    output_dir = "origin_output_json"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all files in input directory
    input_files = []
    for file in os.listdir(input_dir):
        if file.endswith('.json') and file.startswith('state_result_'):
            input_files.append(os.path.join(input_dir, file))
    
    print(f"Found {len(input_files)} files to convert")
    
    success_count = 0
    for input_file in input_files:
        # Generate output filename
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        
        if convert_file_to_json(input_file, output_file):
            success_count += 1
    
    print(f"\n🎉 Conversion complete! {success_count}/{len(input_files)} files converted successfully")
    print(f"Converted files saved in: {output_dir}")

def show_sample_output():
    """Show a sample of the converted JSON structure"""
    output_dir = "origin_output_json"
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        if files:
            sample_file = os.path.join(output_dir, files[0])
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("\n📋 Sample JSON structure:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")

if __name__ == "__main__":
    print("Starting simple conversion of output files to JSON format...")
    convert_all_files()
    show_sample_output() 