# Resume-Job Matching System with Pydantic AI

A Python-based system that uses Pydantic AI to analyze and match resumes with job descriptions. The system provides detailed analysis including whether a candidate is a good match and why, with structured output using Pydantic models.

## Features

- **Pydantic AI Integration**: Uses Pydantic AI for structured LLM interactions
- **Structured Output**: Returns Pydantic models with validated data
- **Flexible Input**: Accepts both PDF and text files for job descriptions and resumes
- **Configurable Prompts**: Customizable prompt templates via YAML configuration
- **Comprehensive Logging**: Built-in logging with Logfire integration
- **Easy Testing**: Includes test samples and test scripts
- **Command Line Interface**: Simple CLI for quick analysis
- **Web UI**: Gradio-based web interface for interactive analysis

## System Architecture

```
hr-agent/
├── config.yaml                    # Configuration file with prompt templates and folder paths
├── resume_analyzer.py             # Main ResumeAnalyzer class (Pydantic AI)
├── file_cache_manager.py          # FileCacheManager for in-memory file caching
├── router.py                      # Router class for analysis orchestration
├── main.py                        # Command-line interface with cache support
├── gradio_ui.py                   # Gradio web interface
├── launch_ui.py                   # Simple UI launcher script
├── example_pydantic_ai.py         # Example demonstrating Pydantic AI usage
├── example_cache_usage.py         # Example demonstrating cache functionality
├── example_router_usage.py        # Example demonstrating Router usage
├── test_resume_matcher.py         # Test script with sample data
├── requirements.txt               # Python dependencies
├── test_samples/                  # Sample files for testing
│   ├── sample_job_description.txt
│   ├── sample_resume_matching.txt
│   └── sample_resume_non_matching.txt
└── data/                          # Your actual data (optional)
    ├── JDs/                       # Job descriptions
    └── Resumes/                   # Resumes
```

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the hr-agent directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Verify configuration**:
   The `config.yaml` file should be properly configured with your LLM settings.

## Usage

### Command Line Interface

The easiest way to use the system:

```bash
# List all available files in cache
python main.py --list

# Show cache statistics
python main.py --stats

# Fetch and display a job description by key
python main.py --jd "Senior Python Developer Job Description Template"

# Analyze a resume against a job description (using JD key and resume name)
python main.py --jd "Senior Python Developer Job Description Template" --resume "resume-001"

# Use custom config file
python main.py --jd "job_key" --resume "resume_name" --config "my_config.yaml"
```

### Programmatic Usage with Cache

```python
import yaml
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

# Load configuration
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Initialize cache manager
jd_folder = config['folders']['job_descriptions']
resume_folder = config['folders']['resumes']
cache_manager = FileCacheManager(jd_folder, resume_folder)

# Get content from cache
jd_content = cache_manager.get_jd_content("job_name")
resume_content = cache_manager.get_resume_content("resume_name")

# Initialize analyzer
analyzer = ResumeAnalyzer("config.yaml")

# Analyze using cached content
import asyncio
result = asyncio.run(analyzer.analyze_resume(jd_content, resume_content))

# Print results (Pydantic model)
print(f"Name: {result.name}")
print(f"Match: {'YES' if result.match else 'NO'}")
print(f"Summary: {result.summary}")

# Access as dictionary
result_dict = result.model_dump()
print(f"As dict: {result_dict}")

# Access as JSON
result_json = result.model_dump_json()
print(f"As JSON: {result_json}")
```

### Async Usage with Pydantic AI

```python
import asyncio
from resume_analyzer import ResumeAnalyzer

async def analyze():
    analyzer = ResumeAnalyzer("config.yaml")
    
    job_description = "We are looking for a Python developer..."
    resume_text = "John Smith, Senior Developer..."
    
    # Pydantic AI automatically returns structured output
    result = await analyzer.analyze_resume(job_description, resume_text)
    return result

# Run the analysis
result = asyncio.run(analyze())
print(f"Structured result: {result.model_dump()}")
```

### Web Interface

The system includes a Gradio-based web interface for interactive analysis:

```bash
# Launch the web UI
python launch_ui.py

# Or directly
python gradio_ui.py
```

The web interface provides:
- **Left Panel**: Job description selection and content preview
- **Right Panel**: Analysis results with tabs for:
  - Results table with match status
  - Detailed analysis with expandable summaries
  - Downloadable markdown reports

Features:
- Dropdown to select from available job descriptions
- Real-time content preview when selecting a JD
- One-click analysis of all resumes against selected JD
- Interactive results with expandable detailed analysis
- Download analysis reports as markdown files

## Configuration

The `config.yaml` file contains prompt templates, folder paths, and logging configuration:

```yaml
# LLM Configuration (handled by Pydantic AI)
llm:
  provider: "openai"  # or "azure_openai" for Azure AI Foundry
  model: "gpt-4o"     # For Azure, this should be your deployment name
  temperature: 0.1
  max_tokens: 1000

# Folder Configuration
folders:
  job_descriptions: "data/JDs"
  resumes: "data/Resumes"

# Prompt Templates
prompts:
  resume_analysis: |
    You are an expert HR recruiter and resume analyst...
    [Your custom prompt template]

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "resume_matcher.log"
```

### Using Azure OpenAI (Azure AI Foundry)

To use Azure OpenAI as your LLM provider, set the following environment variables **before running your app**:

```sh
export AZURE_OPENAI_API_KEY="<your-azure-openai-api-key>"
export AZURE_OPENAI_ENDPOINT="<your-azure-endpoint>"
export AZURE_OPENAI_API_VERSION="2025-01-01-preview"  # Optional, defaults to this value
```

- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure endpoint, e.g. `https://your-resource.openai.azure.com/openai/deployments/<deployment-name>/chat/completions?api-version=2025-01-01-preview`
- `AZURE_OPENAI_API_VERSION`: (Optional) API version, defaults to `2025-01-01-preview`

**Example:**
```sh
export AZURE_OPENAI_API_KEY="ArkYjTtoYuQUFbZvRq43iM9EQTUqAfRgdYqBVMQqov66HYAIAkKcJQQJ99BGACYeBjFXJ3w3AAABACOGMhz0"
export AZURE_OPENAI_ENDPOINT="https://resume-review.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
```

**Note:** The environment variable names must match exactly as above.

### Switching between OpenAI and Azure OpenAI
- To use OpenAI: set `provider: "openai"` in `config.yaml` and set `OPENAI_API_KEY` in your environment.
- To use Azure OpenAI: set `provider: "azure_openai"` in `config.yaml` and set the Azure environment variables as above.

**Note**: Pydantic AI handles the LLM configuration automatically. The `llm` section in config.yaml is kept for reference but not used by the current implementation.

## Output Format

The system outputs structured results using Pydantic models:

```python
class AnalysisResult(BaseModel):
    name: str = Field(description="Full name of the person from the resume")
    match: bool = Field(description="Whether the resume matches the job description")
    summary: str = Field(description="Detailed explanation of why it matches or doesn't match")
```

The result can be accessed as:
- Object attributes: `result.name`, `result.match`, `result.summary`
- Dictionary: `result.model_dump()`
- JSON: `result.model_dump_json()`

### Example Output

```
NAME: John Smith
MATCH: YES
SUMMARY: John Smith is an excellent match for this Senior Python Developer position. 
He has 6+ years of Python development experience, strong expertise in Django, Flask, 
and FastAPI frameworks, and extensive experience with PostgreSQL, MySQL, and cloud 
platforms like AWS. His experience with Docker, Kubernetes, and CI/CD pipelines 
directly aligns with the job requirements. Additionally, he has a Computer Science 
degree and relevant certifications.
```

## Testing

Run the test suite to verify the system works correctly:

```bash
python test_resume_matcher.py
```

The test suite includes:
- **Test 1**: Matching resume (should return YES)
- **Test 2**: Non-matching resume (should return NO)
- **Test 3**: Existing files in data directory (if available)

## Sample Files

The system includes sample files for testing:

- `test_samples/sample_job_description.txt`: Senior Python Developer job description
- `test_samples/sample_resume_matching.txt`: Resume that should match the job
- `test_samples/sample_resume_non_matching.txt`: Marketing resume that shouldn't match

## Logging

The system uses comprehensive logging with Logfire integration:

- **File Logging**: All logs are saved to `resume_matcher.log`
- **Console Logging**: Important messages are also displayed in the console
- **Structured Logging**: Logs include timestamps, log levels, and context

Example log entries:
```
2024-01-15 10:30:15 - resume_analyzer - INFO - ResumeAnalyzer initialized successfully
2024-01-15 10:30:16 - resume_analyzer - INFO - Starting resume analysis
2024-01-15 10:30:18 - resume_analyzer - INFO - Analysis completed for John Smith: Match=True
```

## Error Handling

The system includes robust error handling:

- **File Not Found**: Graceful handling of missing files
- **PDF Extraction Errors**: Fallback for corrupted or unreadable PDFs
- **LLM API Errors**: Proper error messages for API issues
- **Configuration Errors**: Clear error messages for misconfigured YAML

## Customization

### Adding New LLM Providers

To add support for new LLM providers, modify the `_setup_llm()` method in `ResumeAnalyzer`:

```python
def _setup_llm(self):
    llm_config = self.config['llm']
    
    if llm_config['provider'] == 'openai':
        # OpenAI setup
    elif llm_config['provider'] == 'anthropic':
        # Anthropic setup
    elif llm_config['provider'] == 'custom':
        # Custom provider setup
```

### Custom Prompt Templates

Modify the prompt template in `config.yaml` to customize the analysis:

```yaml
prompts:
  resume_analysis: |
    [Your custom prompt with {job_description} and {resume_text} placeholders]
```

### Output Format Customization

Modify the `_parse_llm_response()` method to change the output format:

```python
def _parse_llm_response(self, response: str) -> AnalysisResult:
    # Custom parsing logic
    pass
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is set in the `.env` file
2. **PDF Reading Error**: Some PDFs may have poor text extraction; try converting to text
3. **Configuration Error**: Check that `config.yaml` is properly formatted
4. **Memory Error**: For large files, consider chunking the text

### Performance Tips

- Use text files instead of PDFs for better performance
- Adjust `max_tokens` in config for longer/shorter responses
- Set appropriate `temperature` for more/less creative responses

## Contributing

Feel free to extend the system with additional features:

- Support for more LLM providers
- Additional output formats (JSON, CSV)
- Batch processing capabilities
- Web interface
- Integration with ATS systems

## License

This project is open source and available under the MIT License. 

# HR Analyst Agent

A Gradio-based app for analyzing resumes against job descriptions, generating interview questions, and providing interactive analysis.

---

## 🚀 Deployment & Packaging Guide

Follow these steps to package and deploy this app on a server:

### 1. Clean Up and Prepare Your Codebase
- Ensure your code works locally and all dependencies are in `requirements.txt`.
- Remove debug/test code.

### 2. Create a `requirements.txt`
- List all Python dependencies, e.g.:
  ```
  gradio>=4.0.0
  openai
  PyPDF2
  pydantic
  # ...any others your code uses
  ```

### 3. Add a `README.md`
- (You are here!)
- Briefly describe your app, how to install dependencies, and how to run it.

### 4. (Optional) Add a `Dockerfile`
- For containerized deployment:
  ```dockerfile
  FROM python:3.10
  WORKDIR /app
  COPY . .
  RUN pip install --upgrade pip && pip install -r requirements.txt
  EXPOSE 7860
  CMD ["python", "launch_ui.py"]
  ```

### 5. Test in a Clean Environment
- Create a new virtual environment (or use Docker).
- Install dependencies:
  ```
  pip install -r requirements.txt
  ```
- Run your app:
  ```
  python launch_ui.py
  ```
- Make sure it works as expected.

### 6. Choose a Hosting Option
- **Cloud VM (AWS EC2, DigitalOcean, Azure, etc.):**
  - SSH into your server.
  - Install Python, pip, and git.
  - Clone your repo and install dependencies.
- **PaaS (Heroku, Render, etc.):**
  - Follow their Python app deployment guides.
- **Docker:**
  - Build and run your container:
    ```
    docker build -t hr-agent .
    docker run -p 7860:7860 hr-agent
    ```

### 7. Open Firewall/Ports
- Make sure port 7860 (or your chosen port) is open to the web.

### 8. Run Your App
- On the server, run:
  ```
  python launch_ui.py
  ```
- Or, if using Docker:
  ```
  docker run -p 7860:7860 hr-agent
  ```

### 9. (Optional) Use a Production Web Server
- For more robust deployments, use a reverse proxy (e.g., Nginx) to forward traffic to your Gradio app.
- For HTTPS, set up SSL (Let’s Encrypt, etc.).

### 10. (Optional) Set Up as a System Service
- Use `systemd` or `supervisor` to keep your app running after logout or server restart.

### 11. Access Your App
- Visit `http://<your-server-ip>:7860` in your browser.

### 12. (Optional) Add Authentication
- For public deployments, consider adding a login or password to your Gradio app for security.

---

## Summary Checklist
- [x] Clean code and requirements.txt
- [x] README.md
- [x] (Optional) Dockerfile
- [x] Test in clean environment
- [x] Deploy to server/cloud
- [x] Open port 7860
- [x] Run app and verify
- [x] (Optional) Reverse proxy/SSL
- [x] (Optional) System service
- [x] (Optional) Authentication

---

**Let us know if you need a sample Dockerfile, Nginx config, or step-by-step for a specific cloud provider!** 