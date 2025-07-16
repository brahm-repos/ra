#!/usr/bin/env python3
"""
Test script for the Resume-Job Matching System with File Cache Manager.
"""

import sys
import os
import yaml
from pathlib import Path
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

def load_config(config_path: str):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"Error loading config file: {e}")

def test_cache_manager():
    """Test the FileCacheManager functionality."""
    print("="*60)
    print("TEST 1: FILE CACHE MANAGER")
    print("="*60)
    
    try:
        # Load configuration
        config = load_config("config.yaml")
        jd_folder = config.get('folders', {}).get('job_descriptions', 'data/JDs')
        resume_folder = config.get('folders', {}).get('resumes', 'data/Resumes')
        
        # Initialize cache manager
        cache_manager = FileCacheManager(jd_folder, resume_folder)
        
        # Show cache statistics
        stats = cache_manager.get_cache_stats()
        print(f"Cache Statistics:")
        print(f"  - Job Descriptions: {stats['jd_count']}")
        print(f"  - Resumes: {stats['resume_count']}")
        print(f"  - Total Files: {stats['total_files']}")
        
        # List available files
        print(f"\nAvailable Job Descriptions:")
        for jd_name in cache_manager.get_all_jd_names():
            print(f"  - {jd_name}")
        
        print(f"\nAvailable Resumes:")
        for resume_name in cache_manager.get_all_resume_names():
            print(f"  - {resume_name}")
        
        print("\n✅ TEST PASSED: FileCacheManager initialized successfully")
        
        return cache_manager
        
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        return None

def test_matching_resume(cache_manager):
    """Test with a resume that should match the job description."""
    print("\n" + "="*60)
    print("TEST 2: MATCHING RESUME")
    print("="*60)
    
    try:
        # Get sample content from cache or test files
        jd_content = cache_manager.get_jd_content("sample_job_description")
        resume_content = cache_manager.get_resume_content("sample_resume_matching")
        
        # If not in cache, load from test files
        if not jd_content:
            with open("test_samples/sample_job_description.txt", 'r') as f:
                jd_content = f.read()
        
        if not resume_content:
            with open("test_samples/sample_resume_matching.txt", 'r') as f:
                resume_content = f.read()
        
        # Load config and initialize analyzer
        config = load_config("config.yaml")
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        analyzer = ResumeAnalyzer(prompt_template, model, api_key)
        
        # Analyze using cached content
        import asyncio
        result = asyncio.run(analyzer.analyze_resume(jd_content, resume_content))
        
        print(f"Name: {result.name}")
        print(f"Match: {'YES' if result.match else 'NO'}")
        print(f"\nSummary:")
        print(result.summary)
        
        if result.match:
            print("\n✅ TEST PASSED: Resume correctly identified as a match")
        else:
            print("\n❌ TEST FAILED: Resume should have been a match")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")

def test_non_matching_resume(cache_manager):
    """Test with a resume that should NOT match the job description."""
    print("\n" + "="*60)
    print("TEST 3: NON-MATCHING RESUME")
    print("="*60)
    
    try:
        # Get sample content from cache or test files
        jd_content = cache_manager.get_jd_content("sample_job_description")
        resume_content = cache_manager.get_resume_content("sample_resume_non_matching")
        
        # If not in cache, load from test files
        if not jd_content:
            with open("test_samples/sample_job_description.txt", 'r') as f:
                jd_content = f.read()
        
        if not resume_content:
            with open("test_samples/sample_resume_non_matching.txt", 'r') as f:
                resume_content = f.read()
        
        # Load config and initialize analyzer
        config = load_config("config.yaml")
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        analyzer = ResumeAnalyzer(prompt_template, model, api_key)
        
        # Analyze using cached content
        import asyncio
        result = asyncio.run(analyzer.analyze_resume(jd_content, resume_content))
        
        print(f"Name: {result.name}")
        print(f"Match: {'YES' if result.match else 'NO'}")
        print(f"\nSummary:")
        print(result.summary)
        
        if not result.match:
            print("\n✅ TEST PASSED: Resume correctly identified as not a match")
        else:
            print("\n❌ TEST FAILED: Resume should not have been a match")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")

def test_with_cached_files(cache_manager):
    """Test with files loaded in cache."""
    print("\n" + "="*60)
    print("TEST 4: CACHED FILES")
    print("="*60)
    
    try:
        jd_names = cache_manager.get_all_jd_names()
        resume_names = cache_manager.get_all_resume_names()
        
        if not jd_names or not resume_names:
            print("No files found in cache. Skipping cached files test.")
            return
        
        # Use first available files
        jd_name = jd_names[0]
        resume_name = resume_names[0]
        
        print(f"Testing with JD: {jd_name}")
        print(f"Testing with Resume: {resume_name}")
        
        # Get content from cache
        jd_content = cache_manager.get_jd_content(jd_name)
        resume_content = cache_manager.get_resume_content(resume_name)
        
        if not jd_content or not resume_content:
            print("Could not retrieve content from cache.")
            return
        
        # Load config and initialize analyzer
        config = load_config("config.yaml")
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        analyzer = ResumeAnalyzer(prompt_template, model, api_key)
        
        # Analyze using cached content
        import asyncio
        result = asyncio.run(analyzer.analyze_resume(jd_content, resume_content))
        
        print(f"Name: {result.name}")
        print(f"Match: {'YES' if result.match else 'NO'}")
        print(f"\nSummary:")
        print(result.summary)
        
        print("\n✅ TEST PASSED: Successfully analyzed cached files")
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")

def main():
    """Run all tests."""
    print("RESUME-JOB MATCHING SYSTEM - TEST SUITE")
    print("="*60)
    
    # Check if config file exists
    if not Path("config.yaml").exists():
        print("❌ ERROR: config.yaml not found. Please create the configuration file.")
        sys.exit(1)
    
    # Run tests
    cache_manager = test_cache_manager()
    
    if cache_manager:
        test_matching_resume(cache_manager)
        test_non_matching_resume(cache_manager)
        test_with_cached_files(cache_manager)
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main() 