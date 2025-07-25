import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import re
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.settings import ModelSettings


class AnalysisResult(BaseModel):
    """Result of resume analysis using Pydantic."""
    name: str = Field(description="Full name of the person from the resume")
    match: bool = Field(description="Whether the resume matches the job description")
    summary: str = Field(description="Detailed explanation of why it matches or doesn't match")

class ResumeAnalyzer(Agent):
    """
    Main class for analyzing resumes against job descriptions using Pydantic AI.
    """
    
    # Configure the LLM for Pydantic AI
    model = "gpt-4o"
    
    def __init__(self, prompt_template: dict, model: str, api_key: str, logger: logging.Logger = None, config: dict = None):
        """
        Initialize the ResumeAnalyzer with configuration.
        
        Args:
            prompt_template: The prompt template for resume analysis
            model: The model to use for analysis (deployment name for Azure)
            api_key: (deprecated, kept for compatibility)
            logger: Logger instance (optional)
            config: Full configuration dictionary (should include LLM settings)
        """
        self.prompt_template = prompt_template  # Now a dict with 'system' and 'user'
        self.logger = logger or logging.getLogger(__name__)
        self.config = config  # Store the full config for access to interview_questions

        import os
        llm_conf = (config or {}).get('llm', {})
        provider = llm_conf.get('provider', 'openai')
        deployment_name = llm_conf.get('model', 'gpt-4o')

        if provider == "azure_openai":
            from openai import AsyncAzureOpenAI
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
            # Read timeout from config, default to 60 seconds if not set
            timeout = llm_conf.get('timeout', 60)
            
            if not (azure_endpoint and api_key):
                raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in environment for Azure OpenAI.")
            
            # Create AsyncAzureOpenAI client with timeout
            azure_client = AsyncAzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
                timeout=timeout,  # Set timeout directly on the client
            )
            
            model_obj = OpenAIModel(
                deployment_name,
                provider=AzureProvider(
                    openai_client=azure_client,  # Pass the client with timeout
                ),
            )
            # Log or print the endpoint being used
            msg = f"Using Azure OpenAI endpoint: {azure_endpoint} (API version: {api_version}, timeout: {timeout}s)"
            if self.logger:
                self.logger.info(msg)
            else:
                print(msg)
        else:
            # Default to OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY must be set in environment for OpenAI provider.")
            model_obj = OpenAIModel(deployment_name, api_key=api_key)
            # Log or print the OpenAI usage
            msg = "Using OpenAI API (endpoint managed by OpenAI SDK)"
            if self.logger:
                self.logger.info(msg)
            else:
                print(msg)

        super().__init__(model_obj)
        self.logger.info(f"ResumeAnalyzer initialized successfully with provider: {provider}")
    


    
    async def analyze_resume(
        self, 
        job_description: str, 
        resume_text: str
    ) -> AnalysisResult:
        """
        Analyze a resume against a job description using Pydantic AI.
        
        Args:
            job_description: Job description text
            resume_text: Resume text
            
        Returns:
            AnalysisResult: Analysis result
        """
        try:
            self.logger.info("Starting resume analysis with Pydantic AI")
            
            # Use system and user prompts
            system_prompt = self.prompt_template['system']
            user_prompt = self.prompt_template['user'].format(
                job_description=job_description,
                resume_text=resume_text
            )
            prompt = f"{system_prompt}\n\n{user_prompt}"

            # DEBUG: Log prompt and model details
            self.logger.debug(f"LLM Model: {self.model}")
            if hasattr(self, 'config') and self.config and 'llm' in self.config:
                llm_conf = self.config['llm']
                self.logger.debug(f"LLM Config: {llm_conf}")
            import os
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or os.environ.get("OPENAI_API_BASE")
            self.logger.debug(f"LLM Endpoint: {endpoint}")
            self.logger.debug(f"Prompt sent to LLM:\n{prompt}")
            
            # Use Pydantic AI's run method to get structured output with model from config
            timeout = llm_conf.get('timeout', 60)
            agent_result = await self.run(prompt, model=self.model)
            
            # Debug: Log the structure of the result
            self.logger.debug(f"Agent result type: {type(agent_result)}")
            self.logger.debug(f"Agent result attributes: {dir(agent_result)}")
            
            # Extract the output from AgentRunResult
            if hasattr(agent_result, 'output'):
                output_text = agent_result.output
                self.logger.debug(f"LLM Raw Output:\n{output_text}")
                self.logger.info(f"Extracted output type: {type(output_text)}")
            else:
                self.logger.error("No output found in agent result")
                raise ValueError("No output found in agent result")
            
            # Parse the string output into AnalysisResult
            result = self._parse_output_to_analysis_result(output_text)
            
            self.logger.info(f"Analysis completed for {result.name}: Match={result.match}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during resume analysis: {e}", exc_info=True)
            raise
    
    def _parse_output_to_analysis_result(self, output_text: str) -> AnalysisResult:
        """
        Parse the LLM output text into an AnalysisResult object.
        
        Args:
            output_text: The raw text output from the LLM
            
        Returns:
            AnalysisResult: Parsed analysis result
        """
        try:
            name = "Unknown"
            # Pattern 1: '**Candidate Name:** <Name>'
            match = re.search(r"\*\*Candidate Name:\*\*\s*(.+)", output_text)
            if match:
                name = match.group(1).strip()
            else:
                # Pattern 2: 'is <Name>.'
                match = re.search(r"is ([A-Z][a-zA-Z\s\-']+)\.", output_text)
                if match:
                    name = match.group(1).strip()
                else:
                    # Pattern 3: 'a: Extracted (Person's )?Name\n<Name>' (name on next line)
                    match = re.search(r"a:\s*Extracted (?:Person'?s )?Name\s*\n([A-Z][a-zA-Z\s\-']+)", output_text)
                    if match:
                        name = match.group(1).strip()
                    else:
                        # Pattern 4: 'a: Person's Name\n<Name>' (name on next line)
                        match = re.search(r"a:\s*Person'?s Name\s*\n([A-Z][a-zA-Z\s\-']+)", output_text)
                        if match:
                            name = match.group(1).strip()
                        else:
                            # Pattern 5: Try to find the header and extract the next non-empty line as the name
                            lines = output_text.splitlines()
                            for i, line in enumerate(lines):
                                if re.match(r"a:\s*(Extracted )?(Person'?s )?Name", line.strip()):
                                    # Try next 1-2 lines for a likely name
                                    for j in range(1, 3):
                                        if i + j < len(lines):
                                            possible = lines[i + j].strip()
                                            if possible and re.match(r"^[A-Z][a-zA-Z\s\-']+$", possible):
                                                name = possible
                                                break
                                    if name != "Unknown":
                                        break
            
            # Determine match based on conclusion
            match_bool = False
            conclusion_lower = output_text.lower()
            
            # Look for positive indicators
            positive_indicators = [
                "strong candidate", "good match", "well qualified", "excellent fit",
                "recommended", "suitable", "qualified", "matches", "aligns well"
            ]
            
            # Look for negative indicators
            negative_indicators = [
                "not a match", "does not match", "lacks", "gap", "missing",
                "not suitable", "not qualified", "weak candidate", "does not align"
            ]
            
            positive_count = sum(1 for indicator in positive_indicators if indicator in conclusion_lower)
            negative_count = sum(1 for indicator in negative_indicators if indicator in conclusion_lower)
            
            # Determine match based on indicators
            if positive_count > negative_count:
                match_bool = True
            elif "conclusion" in conclusion_lower:
                # Look specifically in conclusion section
                conclusion_start = conclusion_lower.find("conclusion")
                if conclusion_start != -1:
                    conclusion_text = conclusion_lower[conclusion_start:]
                    if any(indicator in conclusion_text for indicator in positive_indicators):
                        match_bool = True
            
            # Create summary (use the full output as summary)
            summary = output_text.strip()
            
            return AnalysisResult(
                name=name,
                match=match_bool,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing output: {e}")
            # Return a default result if parsing fails
            return AnalysisResult(
                name="Unknown",
                match=False,
                summary=f"Error parsing analysis result: {output_text[:200]}..."
            )
    
    async def generate_interview_questions(self, job_description: str) -> str:
        prompts = self.config['prompts']['interview_questions']
        system_prompt = prompts['system']
        user_prompt = prompts['user'].format(job_description=job_description)
        prompt = f"{system_prompt}\n\n{user_prompt}"
        timeout = (self.config or {}).get('llm', {}).get('timeout', 60)
        agent_result = await self.run(prompt, model=self.model)
        if hasattr(agent_result, 'output'):
            return agent_result.output
        return str(agent_result)
    
  