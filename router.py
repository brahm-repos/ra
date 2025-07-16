#!/usr/bin/env python3
"""
Router class for Resume-Job Matching System with File Cache Manager.
"""

import sys
import os
import yaml
import logging
from pathlib import Path
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

class Router:
    """
    Router class for handling resume analysis requests.
    """
    
    def __init__(self, cache_manager: FileCacheManager, analyzer: ResumeAnalyzer, config: dict, logger: logging.Logger = None):
        """
        Initialize the Router with external components.
        
        Args:
            cache_manager: FileCacheManager instance
            analyzer: ResumeAnalyzer instance
            config: Configuration dictionary
            logger: Logger instance (optional)
        """
        self.cache_manager = cache_manager
        self.analyzer = analyzer
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
    

    
    def get_available_jds(self):
        """Get list of available job description keys."""
        return sorted(self.cache_manager.get_all_jd_names())
    
    def get_cache_stats(self):
        """Get cache statistics."""
        return self.cache_manager.get_cache_stats()
    
    def analyze_jd(self, jd_name: str, verbose: bool = True):
        """
        Analyze a job description against all resumes as a generator.
        Yields (results_list, current_resume_name) after each resume is analyzed.
        """
        # Get JD content from cache
        jd_content = self.cache_manager.get_jd_content(jd_name)
        
        if not jd_content:
            available_jds = self.get_available_jds()
            raise ValueError(f"Job description '{jd_name}' not found. Available: {available_jds}")
        
        # Get all available resumes
        resume_names = self.cache_manager.get_all_resume_names()
        
        if not resume_names:
            raise ValueError("No resumes found in cache.")
        
        if verbose:
            print(f"\n" + "="*60)
            print(f"ANALYZING JD: {jd_name}")
            print(f"AGAINST {len(resume_names)} RESUMES")
            print("="*60)
        
        # Initialize results list to store all analysis results
        results_list = []
        
        # Analyze against all resumes
        import asyncio
        
        for i, resume_name in enumerate(resume_names, 1):
            if verbose:
                print(f"\n{i}. Analyzing Resume: {resume_name}")
                print("-" * 40)
            
            resume_content = self.cache_manager.get_resume_content(resume_name)
            
            if resume_content:
                try:
                    result = asyncio.run(self.analyzer.analyze_resume(jd_content, resume_content))
                    
                    # Store result in list
                    result_dict = {
                        'resume_name': resume_name,
                        'candidate_name': result.name,
                        'match': result.match,
                        'summary': result.summary,
                        'status': 'SUCCESS'
                    }
                    results_list.append(result_dict)
                    
                    if verbose:
                        print(f"Name: {result.name}")
                        print(f"Match: {'YES' if result.match else 'NO'}")
                        print(f"Summary: {result.summary[:200]}...")
                        
                        if result.match:
                            print("✅ MATCH")
                        else:
                            print("❌ NO MATCH")
                        
                except Exception as e:
                    error_msg = f"Error analyzing {resume_name}: {e}"
                    if verbose:
                        print(error_msg)
                    
                    # Store error result
                    result_dict = {
                        'resume_name': resume_name,
                        'candidate_name': 'Unknown',
                        'match': False,
                        'summary': error_msg,
                        'status': 'ERROR'
                    }
                    results_list.append(result_dict)
            else:
                error_msg = f"Could not retrieve content for {resume_name}"
                if verbose:
                    print(error_msg)
                
                # Store error result
                result_dict = {
                    'resume_name': resume_name,
                    'candidate_name': 'Unknown',
                    'match': False,
                    'summary': error_msg,
                    'status': 'ERROR'
                }
                results_list.append(result_dict)
            
            # After each resume, yield progress
            yield list(results_list), resume_name
        # At the end, yield the final result
        table_data = self._generate_table(results_list, verbose)
        statistics = self._calculate_statistics(results_list)
        yield {
            'jd_name': jd_name,
            'results': results_list,
            'table': table_data,
            'statistics': statistics
        }, None
    
    def _generate_table(self, results_list, verbose=True):
        """Generate tabular representation of results."""
        table_lines = []
        
        if verbose:
            table_lines.append("="*80)
            table_lines.append("ANALYSIS SUMMARY TABLE")
            table_lines.append("="*80)
        
        # Header
        header = f"{'#':<3} {'Resume Name':<25} {'Candidate Name':<20} {'Match':<8} {'Status':<10}"
        table_lines.append(header)
        table_lines.append("-" * 80)
        
        # Results
        for i, result in enumerate(results_list, 1):
            match_status = "✅ YES" if result['match'] else "❌ NO"
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            
            row = f"{i:<3} {result['resume_name']:<25} {result['candidate_name']:<20} {match_status:<8} {status_icon} {result['status']:<10}"
            table_lines.append(row)
        
        return table_lines
    
    def _calculate_statistics(self, results_list):
        """Calculate statistics from results."""
        total_analyzed = len(results_list)
        successful_matches = sum(1 for r in results_list if r['match'] and r['status'] == 'SUCCESS')
        total_successful = sum(1 for r in results_list if r['status'] == 'SUCCESS')
        total_errors = sum(1 for r in results_list if r['status'] == 'ERROR')
        
        match_rate = (successful_matches/total_successful*100) if total_successful > 0 else 0
        
        return {
            'total_analyzed': total_analyzed,
            'successful_matches': successful_matches,
            'total_successful': total_successful,
            'total_errors': total_errors,
            'match_rate': match_rate
        }
    
    def print_summary(self, analysis_result):
        """Print the complete analysis summary."""
        # Print table
        for line in analysis_result['table']:
            print(line)
        
        # Print statistics
        stats = analysis_result['statistics']
        print("-" * 80)
        print(f"SUMMARY STATISTICS:")
        print(f"  - Total Resumes Analyzed: {stats['total_analyzed']}")
        print(f"  - Successful Matches: {stats['successful_matches']}")
        print(f"  - Successful Analyses: {stats['total_successful']}")
        print(f"  - Errors: {stats['total_errors']}")
        print(f"  - Match Rate: {stats['match_rate']:.1f}%" if stats['total_successful'] > 0 else "  - Match Rate: N/A")
        print("="*80)


def main():
    """Main function for command-line usage."""
    import argparse
    from main import load_config, setup_logging
    
    parser = argparse.ArgumentParser(description="Resume-Job Matching System Router")
    parser.add_argument("--jd", required=True, help="JD key/name to fetch from cache")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--list", action="store_true", help="List all available files")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    
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
        
        # Initialize router
        router = Router(cache_manager, analyzer, config, logger)
        
        # Handle different commands
        if args.list:
            print("Available Job Description Keys:")
            print("-" * 30)
            for jd_name in router.get_available_jds():
                print(f"  - {jd_name}")
            return
        
        if args.stats:
            stats = router.get_cache_stats()
            print("Cache Statistics:")
            print(f"  - Job Descriptions: {stats['jd_count']}")
            print(f"  - Resumes: {stats['resume_count']}")
            print(f"  - Total Files: {stats['total_files']}")
            return
        
        # Analyze JD
        verbose = not args.quiet
        result = router.analyze_jd(args.jd, verbose=verbose)
        
        # Print summary
        router.print_summary(result)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 