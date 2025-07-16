#!/usr/bin/env python3
"""
Example script demonstrating Pydantic AI usage for resume-job matching.
"""

import asyncio
from resume_analyzer import ResumeAnalyzer, AnalysisResult

async def example_usage():
    """Example of using the Pydantic AI resume analyzer."""
    
    # Load config and initialize the analyzer
    import yaml
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    prompt_template = config.get('prompts', {}).get('resume_analysis', '')
    model = config.get('llm', {}).get('model', 'gpt-4o')
    api_key = config.get('llm', {}).get('api_key')
    analyzer = ResumeAnalyzer(prompt_template, model, api_key)
    
    # Example job description
    job_description = """
    Senior Python Developer
    
    Requirements:
    - 5+ years Python development experience
    - Experience with Django, Flask, or FastAPI
    - Knowledge of PostgreSQL, MySQL
    - Experience with AWS, Azure, or GCP
    - Strong problem-solving skills
    - Experience with Docker and Kubernetes
    - Bachelor's degree in Computer Science
    """
    
    # Example resume that should match
    matching_resume = """
    John Smith
    Senior Software Engineer
    
    Experience:
    - 6 years Python Developer at TechCorp
    - Built web apps with Django and Flask
    - Worked with PostgreSQL and MySQL
    - Deployed on AWS
    - Used Docker for containers
    
    Skills: Python, Django, Flask, PostgreSQL, MySQL, AWS, Docker, Git
    
    Education: Bachelor's in Computer Science
    """
    
    # Example resume that should NOT match
    non_matching_resume = """
    Sarah Johnson
    Marketing Specialist
    
    Experience:
    - 4 years in digital marketing
    - Social media management
    - Google Analytics and Facebook Ads
    - Content creation and SEO
    
    Skills: Marketing, Social Media, Google Analytics, Content Creation
    
    Education: Bachelor's in Marketing
    """
    
    print("="*60)
    print("PYDANTIC AI RESUME ANALYZER EXAMPLE")
    print("="*60)
    
    # Test with matching resume
    print("\n1. Testing with MATCHING resume:")
    print("-" * 40)
    result1 = await analyzer.analyze_resume(job_description, matching_resume)
    print(f"Name: {result1.name}")
    print(f"Match: {'YES' if result1.match else 'NO'}")
    print(f"Summary: {result1.summary}")
    
    # Test with non-matching resume
    print("\n2. Testing with NON-MATCHING resume:")
    print("-" * 40)
    result2 = await analyzer.analyze_resume(job_description, non_matching_resume)
    print(f"Name: {result2.name}")
    print(f"Match: {'YES' if result2.match else 'NO'}")
    print(f"Summary: {result2.summary}")
    
    # Demonstrate Pydantic model features
    print("\n3. Pydantic Model Features:")
    print("-" * 40)
    print(f"Result type: {type(result1)}")
    print(f"Is Pydantic model: {hasattr(result1, 'model_dump')}")
    
    # Convert to dict
    result_dict = result1.model_dump()
    print(f"As dictionary: {result_dict}")
    
    # Convert to JSON
    result_json = result1.model_dump_json()
    print(f"As JSON: {result_json}")

def main():
    """Run the example."""
    asyncio.run(example_usage())

if __name__ == "__main__":
    main() 