#!/usr/bin/env python3
"""
Example script demonstrating Router class usage.
"""

from router import Router
from main import load_config, setup_logging
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

def example_router_usage():
    """Example of using the Router class."""
    
    print("="*60)
    print("ROUTER CLASS USAGE EXAMPLE")
    print("="*60)
    
    try:
        # Load configuration
        config = load_config("config.yaml")
        
        # Setup logging
        logger = setup_logging(config)
        
        # Get folder paths from config
        jd_folder = config.get('folders', {}).get('job_descriptions', 'data/JDs')
        resume_folder = config.get('folders', {}).get('resumes', 'data/Resumes')
        
        # Get prompt template, model, and API key from config
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        
        # Initialize components
        cache_manager = FileCacheManager(jd_folder, resume_folder)
        analyzer = ResumeAnalyzer(prompt_template, model, api_key, logger)
        
        # Initialize router
        router = Router(cache_manager, analyzer, config, logger)
        
        # Get available JDs
        print("\n1. Available Job Descriptions:")
        print("-" * 30)
        jd_names = router.get_available_jds()
        for jd_name in jd_names:
            print(f"  - {jd_name}")
        
        # Get cache statistics
        print("\n2. Cache Statistics:")
        print("-" * 30)
        stats = router.get_cache_stats()
        print(f"  - Job Descriptions: {stats['jd_count']}")
        print(f"  - Resumes: {stats['resume_count']}")
        print(f"  - Total Files: {stats['total_files']}")
        
        # Analyze a specific JD (quiet mode)
        if jd_names:
            print(f"\n3. Analyzing JD: {jd_names[0]} (Quiet Mode)")
            print("-" * 50)
            
            # Analyze without verbose output
            result = router.analyze_jd(jd_names[0], verbose=False)
            
            # Print the results
            print(f"Analysis completed for: {result['jd_name']}")
            print(f"Total results: {len(result['results'])}")
            
            # Print table
            router.print_summary(result)
            
            # Access individual results
            print(f"\n4. Individual Results Access:")
            print("-" * 30)
            for i, res in enumerate(result['results'][:3], 1):  # Show first 3
                print(f"Result {i}:")
                print(f"  - Resume: {res['resume_name']}")
                print(f"  - Candidate: {res['candidate_name']}")
                print(f"  - Match: {'YES' if res['match'] else 'NO'}")
                print(f"  - Status: {res['status']}")
                print()
        
        # Example with verbose mode
        if len(jd_names) > 1:
            print(f"\n5. Analyzing JD: {jd_names[1]} (Verbose Mode)")
            print("-" * 50)
            
            # Analyze with verbose output
            result = router.analyze_jd(jd_names[1], verbose=True)
            
            # Print just the statistics
            stats = result['statistics']
            print(f"\nQuick Stats:")
            print(f"  - Match Rate: {stats['match_rate']:.1f}%")
            print(f"  - Successful Matches: {stats['successful_matches']}")
            print(f"  - Errors: {stats['total_errors']}")
        
        print("\n✅ Router class usage example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_programmatic_usage():
    """Example of programmatic usage without printing."""
    
    print("\n" + "="*60)
    print("PROGRAMMATIC USAGE EXAMPLE")
    print("="*60)
    
    try:
        # Load configuration
        config = load_config("config.yaml")
        
        # Setup logging
        logger = setup_logging(config)
        
        # Get folder paths from config
        jd_folder = config.get('folders', {}).get('job_descriptions', 'data/JDs')
        resume_folder = config.get('folders', {}).get('resumes', 'data/Resumes')
        
        # Get prompt template, model, and API key from config
        prompt_template = config.get('prompts', {}).get('resume_analysis', '')
        model = config.get('llm', {}).get('model', 'gpt-4o')
        api_key = config.get('llm', {}).get('api_key')
        
        # Initialize components
        cache_manager = FileCacheManager(jd_folder, resume_folder)
        analyzer = ResumeAnalyzer(prompt_template, model, api_key, logger)
        
        # Initialize router
        router = Router(cache_manager, analyzer, config, logger)
        
        # Get available JDs
        jd_names = router.get_available_jds()
        
        if not jd_names:
            print("No job descriptions available.")
            return
        
        # Analyze JD and get results as data structure
        result = router.analyze_jd(jd_names[0], verbose=False)
        
        # Work with the data programmatically
        print(f"Analysis Results for: {result['jd_name']}")
        print(f"Total resumes analyzed: {result['statistics']['total_analyzed']}")
        
        # Find all successful matches
        matches = [r for r in result['results'] if r['match'] and r['status'] == 'SUCCESS']
        print(f"Successful matches: {len(matches)}")
        
        # Print match details
        for match in matches:
            print(f"  - {match['candidate_name']} ({match['resume_name']})")
        
        # Find all errors
        errors = [r for r in result['results'] if r['status'] == 'ERROR']
        if errors:
            print(f"\nErrors encountered: {len(errors)}")
            for error in errors:
                print(f"  - {error['resume_name']}: {error['summary']}")
        
        print("\n✅ Programmatic usage example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    example_router_usage()
    example_programmatic_usage() 