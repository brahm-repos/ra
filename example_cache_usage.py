#!/usr/bin/env python3
"""
Example script demonstrating FileCacheManager usage with Resume Analyzer.
"""

import asyncio
import yaml
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

def load_config(config_path: str):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"Error loading config file: {e}")

async def example_cache_usage():
    """Example of using FileCacheManager with ResumeAnalyzer."""
    
    print("="*60)
    print("FILE CACHE MANAGER EXAMPLE")
    print("="*60)
    
    # Load configuration
    config = load_config("config.yaml")
    jd_folder = config.get('folders', {}).get('job_descriptions', 'data/JDs')
    resume_folder = config.get('folders', {}).get('resumes', 'data/Resumes')
    
    print(f"JD Folder: {jd_folder}")
    print(f"Resume Folder: {resume_folder}")
    
    # Initialize cache manager
    print("\nInitializing FileCacheManager...")
    cache_manager = FileCacheManager(jd_folder, resume_folder)
    
    # Show cache statistics
    stats = cache_manager.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  - Job Descriptions: {stats['jd_count']}")
    print(f"  - Resumes: {stats['resume_count']}")
    print(f"  - Total Files: {stats['total_files']}")
    
    # List available files
    print(f"\nAvailable Job Descriptions:")
    jd_names = cache_manager.get_all_jd_names()
    for jd_name in jd_names:
        print(f"  - {jd_name}")
    
    print(f"\nAvailable Resumes:")
    resume_names = cache_manager.get_all_resume_names()
    for resume_name in resume_names:
        print(f"  - {resume_name}")
    
    # Example: Analyze a specific JD and resume
    if jd_names and resume_names:
        print(f"\n" + "="*60)
        print("ANALYZING SPECIFIC FILES")
        print("="*60)
        
        # Use first available files
        jd_name = jd_names[0]
        resume_name = resume_names[0]
        
        print(f"Analyzing JD: {jd_name}")
        print(f"Analyzing Resume: {resume_name}")
        
        # Get content from cache
        jd_content = cache_manager.get_jd_content(jd_name)
        resume_content = cache_manager.get_resume_content(resume_name)
        
        if jd_content and resume_content:
            # Load config and initialize analyzer
            prompt_template = config.get('prompts', {}).get('resume_analysis', '')
            model = config.get('llm', {}).get('model', 'gpt-4o')
            api_key = config.get('llm', {}).get('api_key')
            analyzer = ResumeAnalyzer(prompt_template, model, api_key)
            
            # Analyze using cached content
            result = await analyzer.analyze_resume(jd_content, resume_content)
            
            print(f"\nResults:")
            print(f"Name: {result.name}")
            print(f"Match: {'YES' if result.match else 'NO'}")
            print(f"Summary: {result.summary}")
            
            # Demonstrate Pydantic features
            print(f"\nPydantic Model Features:")
            print(f"  - As dict: {result.model_dump()}")
            print(f"  - As JSON: {result.model_dump_json()}")
        else:
            print("Could not retrieve content from cache.")
    
    # Example: Batch analysis
    print(f"\n" + "="*60)
    print("BATCH ANALYSIS EXAMPLE")
    print("="*60)
    
    if len(jd_names) > 0 and len(resume_names) > 0:
        # Analyze first JD against all resumes
        jd_name = jd_names[0]
        jd_content = cache_manager.get_jd_content(jd_name)
        
        if jd_content:
            # Load config and initialize analyzer
            prompt_template = config.get('prompts', {}).get('resume_analysis', '')
            model = config.get('llm', {}).get('model', 'gpt-4o')
            api_key = config.get('llm', {}).get('api_key')
            analyzer = ResumeAnalyzer(prompt_template, model, api_key)
            
            print(f"Analyzing JD '{jd_name}' against all resumes:")
            
            for i, resume_name in enumerate(resume_names[:3], 1):  # Limit to first 3
                resume_content = cache_manager.get_resume_content(resume_name)
                
                if resume_content:
                    result = await analyzer.analyze_resume(jd_content, resume_content)
                    
                    print(f"\n{i}. Resume: {resume_name}")
                    print(f"   Name: {result.name}")
                    print(f"   Match: {'YES' if result.match else 'NO'}")
                    print(f"   Summary: {result.summary[:100]}...")
    
    # Example: Cache refresh
    print(f"\n" + "="*60)
    print("CACHE REFRESH EXAMPLE")
    print("="*60)
    
    print("Refreshing cache...")
    cache_manager.refresh_cache()
    
    new_stats = cache_manager.get_cache_stats()
    print(f"After refresh - Cache Statistics:")
    print(f"  - Job Descriptions: {new_stats['jd_count']}")
    print(f"  - Resumes: {new_stats['resume_count']}")
    print(f"  - Total Files: {new_stats['total_files']}")

def main():
    """Run the example."""
    asyncio.run(example_cache_usage())

if __name__ == "__main__":
    main() 