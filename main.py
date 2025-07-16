#!/usr/bin/env python3
"""
Main program for Resume-Job Matching System with File Cache Manager.
"""

import argparse
import sys
import os
import yaml
import logging
from pathlib import Path
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager
from router import Router

def load_config(config_path: str):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Replace environment variables
        if config['llm']['api_key'].startswith('${') and config['llm']['api_key'].endswith('}'):
            env_var = config['llm']['api_key'][2:-1]
            config['llm']['api_key'] = os.getenv(env_var)
            
        return config
    except Exception as e:
        raise Exception(f"Error loading config file: {e}")

def setup_logging(config: dict):
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_config.get('file', 'resume_matcher.log')),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Main function to run the resume analyzer."""
    
    parser = argparse.ArgumentParser(description="Resume-Job Matching System")
    parser.add_argument("--jd", help="JD key/name to fetch from cache")
    parser.add_argument("--resume", help="Name of resume file (without extension)")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--list", action="store_true", help="List all available files")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Setup logging
        logger = setup_logging(config)
        
        # Get folder paths from config
        jd_folder = config.get('folders', {}).get('job_descriptions', 'data/JDs')
        resume_folder = config.get('folders', {}).get('resumes', 'data/Resumes')
        
        # Get prompt template, model, and API key from config
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        
        # Validate API key
        if not api_key:
            print("Error: OpenAI API key not found in config or environment variable OPENAI_API_KEY not set.")
            sys.exit(1)
        
        # Initialize components
        cache_manager = FileCacheManager(jd_folder, resume_folder)
        analyzer = ResumeAnalyzer(prompt_template, model, api_key, logger)
        
        # Initialize the router
        router = Router(cache_manager, analyzer, config, logger)
        
        # Show available JD keys if requested
        if args.list:
            print("Available Job Description Keys:")
            print("-" * 30)
            for jd_name in sorted(router.get_available_jds()):
                print(f"  - {jd_name}")
            return
        
        # Show cache statistics if requested
        if args.stats:
            stats = router.get_cache_stats()
            print("Cache Statistics:")
            print(f"  - Job Descriptions: {stats['jd_count']}")
            print(f"  - Resumes: {stats['resume_count']}")
            print(f"  - Total Files: {stats['total_files']}")
            return
        
        # Check if JD is provided when not using --list or --stats
        if not args.jd and not args.list and not args.stats:
            print("Error: --jd argument is required when not using --list or --stats.")
            print("Use --list to see available JD keys.")
            sys.exit(1)
        
        # Analyze JD against all resumes
        if args.jd:
            result = router.analyze_jd(args.jd)
            
            # Print formatted table
            router.print_summary(result)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 