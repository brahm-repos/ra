#!/usr/bin/env python3
"""
Gradio UI for HR Analyst Agent
"""

import gradio as gr
import os
import sys
from pathlib import Path
import markdown
from datetime import datetime

# Import our modules
from main import load_config, setup_logging
from router import Router
from resume_analyzer import ResumeAnalyzer
from file_cache_manager import FileCacheManager

class HRUIManager:
    """Manager class for the HR UI application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the UI manager with configuration."""
        self.config_path = config_path
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config)
        
        # Get folder paths from config
        self.jd_folder = self.config.get('folders', {}).get('job_descriptions', 'data/JDs')
        self.resume_folder = self.config.get('folders', {}).get('resumes', 'data/Resumes')
        
        # Get prompt template, model, and API key from config
        self.prompt_template = self.config.get('prompts', {}).get('resume_analysis', '')
        self.model = self.config.get('llm', {}).get('model', 'gpt-4o')
        self.api_key = self.config.get('llm', {}).get('api_key')
        
        # Validate API key
        if not self.api_key:
            raise ValueError("OpenAI API key not found in config or environment variable OPENAI_API_KEY not set.")
        
        # Initialize components
        self.cache_manager = FileCacheManager(self.jd_folder, self.resume_folder)
        self.analyzer = ResumeAnalyzer(self.prompt_template, self.model, self.api_key, self.logger, self.config)
        self.router = Router(self.cache_manager, self.analyzer, self.config, self.logger)
        
        # Store current analysis results
        self.current_results = None
    
    def get_available_jds(self):
        """Get list of available job descriptions."""
        return self.router.get_available_jds()
    
    def get_jd_content(self, jd_name: str):
        """Get content of a specific job description."""
        if not jd_name:
            return "Please select a job description."
        
        content = self.cache_manager.get_jd_content(jd_name)
        if content:
            return content
        else:
            return f"Could not retrieve content for {jd_name}"
    
    def analyze_jd(self, jd_name: str):
        """Generator: Analyze a job description and yield progress/results after each resume."""
        if not jd_name:
            yield "Please select a job description to analyze.", "", "", "", []
            return
        try:
            gen = self.router.analyze_jd(jd_name, verbose=False)
            for partial_result, resume_name in gen:
                if resume_name is not None:
                    result = {
                        'jd_name': jd_name,
                        'results': partial_result,
                        'table': self._generate_table_html({'results': partial_result}),
                        'statistics': self._calculate_statistics(partial_result)
                    }
                    table_html, detail_buttons = self._generate_table_html(result, progress=f'Processing {resume_name} resume')
                    summary_html = self._generate_summary_html(result)
                    download_content = self._generate_download_content(result)
                    progress = f'Processing {resume_name} resume'
                    yield table_html, summary_html, download_content, progress, detail_buttons
                else:
                    self.current_results = partial_result
                    table_html, detail_buttons = self._generate_table_html(partial_result, progress=None)
                    summary_html = self._generate_summary_html(partial_result)
                    download_content = self._generate_download_content(partial_result)
                    yield table_html, summary_html, download_content, "", detail_buttons
        except Exception as e:
            error_msg = f"Error analyzing {jd_name}: {str(e)}"
            self.logger.error(error_msg)
            yield error_msg, "", "", "", []
    
    def _generate_table_html(self, result, progress=None):
        """Generate HTML table from analysis results and return detail_buttons for Gradio links."""
        if not result or 'results' not in result:
            return "No results available.", []
        import urllib.parse
        import base64
        progress_str = f": <span style='color:#0066cc'>{progress}</span>" if progress else ""
        html = f"""
        <style>
        .modal-gr {{ display: none; position: fixed; z-index: 10000; left: 0; top: 0; width: 100vw; height: 100vh; overflow: auto; background: rgba(0,0,0,0.4); }}
        .modal-content-gr {{ background: #fff; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 600px; border-radius: 5px; position: relative; }}
        .close-gr {{ color: #aaa; position: absolute; right: 16px; top: 8px; font-size: 28px; font-weight: bold; cursor: pointer; }}
        .close-gr:hover {{ color: #000; }}
        </style>
        <div style="font-family: Arial, sans-serif;">
            <h3>Analysis Results{progress_str}</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">#</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Resume Name</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Candidate Name</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Match</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Details</th>
                    </tr>
                </thead>
                <tbody>
        """
        detail_buttons = []
        for i, res in enumerate(result['results'], 1):
            match_status = "✅ YES" if res['match'] else "❌ NO"
            status_icon = "✅" if res['status'] == 'SUCCESS' else "❌"
            status_color = "green" if res['status'] == 'SUCCESS' else "red"
            candidate = res['candidate_name']
            resume = res['resume_name']
            status = res['status']
            match = '✅ MATCH' if res['match'] else '❌ NO MATCH'
            summary = res['summary'].replace('\n', '<br>')
            modal_id = f"modal-gr-{i}"
            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{i}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{resume}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{candidate}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{match_status}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {status_color};">{status_icon} {status}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;"><a href="#" onclick="showModalGr('{modal_id}');return false;">View Details</a></td>
                </tr>
                <div id="{modal_id}" class="modal-gr">
                  <div class="modal-content-gr">
                    <span class="close-gr" onclick="closeModalGr('{modal_id}')">&times;</span>
                    <h3>Review of: {candidate} ({resume})</h3>
                    <p><b>Status:</b> <span style='color:{'green' if status == 'SUCCESS' else 'red'};'>{status}</span></p>
                    <p><b>Match:</b> {match}</p>
                    <div style='margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; white-space: pre-wrap;'>{summary}</div>
                  </div>
                </div>
            """
            detail_buttons.append({'resume': resume, 'candidate': candidate, 'summary': res['summary'], 'status': status, 'match': res['match']})
        html += """
                </tbody>
            </table>
        </div>
        <script>
        function showModalGr(id) {{
            document.getElementById(id).style.display = 'block';
        }}
        function closeModalGr(id) {{
            document.getElementById(id).style.display = 'none';
        }}
        window.onclick = function(event) {{
            var modals = document.getElementsByClassName('modal-gr');
            for (var i = 0; i < modals.length; i++) {{
                if (event.target == modals[i]) {{
                    modals[i].style.display = 'none';
                }}
            }}
        }}
        </script>
        """
        return html, detail_buttons
    
    def _generate_summary_html(self, result):
        """Generate HTML summary with expandable details."""
        if not result or 'results' not in result:
            return "No results available."
        
        html = """
        <div style="font-family: Arial, sans-serif;">
            <h3>Detailed Analysis</h3>
        """
        
        for i, res in enumerate(result['results'], 1):
            match_icon = "✅" if res['match'] else "❌"
            match_text = "MATCH" if res['match'] else "NO MATCH"
            status_color = "green" if res['status'] == 'SUCCESS' else "red"
            
            html += f"""
            <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; padding: 15px;">
                <h4 style="margin: 0 0 10px 0; color: {status_color};">
                    {match_icon} {res['candidate_name']} ({res['resume_name']}) - {match_text}
                </h4>
                <details>
                    <summary style="cursor: pointer; color: #0066cc; font-weight: bold;">
                        Click to view detailed analysis
                    </summary>
                    <div style="margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; white-space: pre-wrap;">
                        {res['summary']}
                    </div>
                </details>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _generate_download_content(self, result):
        """Generate markdown content for download."""
        if not result or 'results' not in result:
            return ""
        
        md_content = f"""# HR Analysis Report

**Job Description:** {result['jd_name']}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- Total Resumes Analyzed: {result['statistics']['total_analyzed']}
- Successful Matches: {result['statistics']['successful_matches']}
- Successful Analyses: {result['statistics']['total_successful']}
- Errors: {result['statistics']['total_errors']}
- Match Rate: {result['statistics']['match_rate']:.1f}%

## Detailed Results

"""
        
        for i, res in enumerate(result['results'], 1):
            match_status = "✅ MATCH" if res['match'] else "❌ NO MATCH"
            md_content += f"""
### {i}. {res['candidate_name']} ({res['resume_name']})

**Status:** {match_status}
**Analysis Status:** {res['status']}

**Detailed Analysis:**
{res['summary']}

---
"""
        
        return md_content

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

def create_ui():
    """Create and return the Gradio interface."""
    
    # Initialize UI manager
    try:
        ui_manager = HRUIManager()
    except Exception as e:
        print(f"Error initializing UI manager: {e}")
        return None
    
    # Get available JDs
    available_jds = ui_manager.get_available_jds()
    if not available_jds:
        available_jds = ["No job descriptions available"]
    # Set default JD
    default_jd = available_jds[0] if available_jds and available_jds[0] != "No job descriptions available" else None
    
    # Create the interface
    with gr.Blocks(title="Tessa", css="""
        .flashing-red {
            color: red;
            animation: flash 1s infinite;
            font-weight: bold;
        }
        @keyframes flash {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        .disabled-tabs {
            pointer-events: none;
            opacity: 0.6;
        }
        .disabled-tabs .tab-nav {
            pointer-events: none;
        }
    """) as interface:
        gr.Markdown("# Tessa (Talent Screening Assistant)")
        
        # Global processing state
        processing_state = gr.State(False)
        
        # JavaScript to control tab navigation
        gr.HTML("""
        <script>
        function disableTabs() {
            const tabs = document.querySelectorAll('.tabs');
            tabs.forEach(tab => {
                tab.classList.add('disabled-tabs');
            });
        }
        
        function enableTabs() {
            const tabs = document.querySelectorAll('.tabs');
            tabs.forEach(tab => {
                tab.classList.remove('disabled-tabs');
            });
        }
        
        // Listen for custom events
        document.addEventListener('processing-start', disableTabs);
        document.addEventListener('processing-end', enableTabs);
        </script>
        """)
        
        with gr.Tabs():
            with gr.TabItem("Screen By JD"):
                with gr.Row():
                    # Left Panel
                    with gr.Column(scale=1):
                        gr.Markdown("## Job Description Selection")
                        with gr.Row():
                            jd_dropdown = gr.Dropdown(
                                choices=available_jds,
                                label="Select JD",
                                interactive=True,
                                value=default_jd
                            )
                        # Dynamic Analyze button label
                        def get_analyze_label(jd_name):
                            if jd_name and jd_name != "No job descriptions available":
                                return f"Analyze Profiles for {jd_name}"
                            return "Analyze"
                        analyze_btn = gr.Button(get_analyze_label(default_jd), variant="primary")
                        # 1. Define the tip as a Markdown component, initially hidden
                        analyze_tip = gr.Markdown("**Tip:** Click the '🔍 Analysis' or '▶ Generate' cell in the table below to see details in the right pane.", visible=False)
                        # 1. Remove 'Candidate Name' column from results_df and all related code
                        results_df = gr.Dataframe(
                            headers=["Resume Name", "Match", "Analysis", "Interview Questions"],
                            interactive=False,
                            datatype=["str", "str", "str", "str"],
                            visible=False
                        )
                        details_state = gr.State([])  # To store detail_buttons data
                        # 1. Add a Markdown component for status/progress above the results table
                        analyze_status = gr.HTML("", visible=False, elem_classes=["flashing-red"])
                        # JavaScript trigger for tab control
                        tab_control_trigger = gr.HTML("", visible=False)
                    # Right Panel
                    with gr.Column(scale=1):
                        if default_jd:
                            default_jd_content = ui_manager.get_jd_content(default_jd)
                            right_header = gr.Markdown(f"## JD: {default_jd}")
                            right_view_md = gr.Markdown(
                                value=f"<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'><pre style='white-space: pre-wrap; margin:0;'>{default_jd_content}</pre></div>",
                                visible=True
                            )
                            chatbox = gr.Chatbot(label="Interview Questions Chat", visible=False, elem_id="interview-questions-chat", type="messages")
                            user_question = gr.Textbox(label="Ask a question about the interview questions", visible=False, placeholder="Type your question and press Enter...")
                            send_btn = gr.Button("Send", visible=False)
                            chat_state = gr.State([])
                            export_btn = gr.Button("Export", visible=False)
                            download_file = gr.File(label="Download Chat", visible=False)
                        else:
                            right_header = gr.Markdown("## Views")
                            right_view_md = gr.Markdown(
                                value="<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'>No job description selected.</div>",
                                visible=True
                            )
                            chatbox = gr.Chatbot(label="Interview Questions Chat", visible=False, elem_id="interview-questions-chat", type="messages")
                            user_question = gr.Textbox(label="Ask a question about the interview questions", visible=False, placeholder="Type your question and press Enter...")
                            send_btn = gr.Button("Send", visible=False)
                            chat_state = gr.State([])
                            export_btn = gr.Button("Export", visible=False)
                            download_file = gr.File(label="Download Chat", visible=False)
                # Event handlers
                def on_jd_select(jd_name):
                    if jd_name and jd_name != "No job descriptions available":
                        content = ui_manager.get_jd_content(jd_name)
                        html_box = f"<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'><pre style='white-space: pre-wrap; margin:0;'>{content}</pre></div>"
                        # Clear right pane, results table, tip, and interview questions/chat area
                        return (
                            gr.update(value=html_box, visible=True),
                            gr.update(value=f"## JD: {jd_name}"),
                            gr.update(value=get_analyze_label(jd_name)),
                            gr.update(value=[], visible=False),  # results_df
                            [],  # details_state
                            gr.update(visible=False),  # analyze_tip
                            gr.update(value=[], visible=False),  # chatbox
                            gr.update(value="", visible=False),  # user_question
                            gr.update(visible=False),  # send_btn
                            gr.update(visible=False),  # export_btn
                            gr.update(visible=False),  # download_file
                            []  # chat_state
                        )
                    # If no JD selected, reset everything
                    return (
                        gr.update(value="<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'>No job description selected.</div>", visible=True),
                        gr.update(value="## Views"),
                        gr.update(value="Analyze"),
                        gr.update(value=[], visible=False),  # results_df
                        [],  # details_state
                        gr.update(visible=False),  # analyze_tip
                        gr.update(value=[], visible=False),  # chatbox
                        gr.update(value="", visible=False),  # user_question
                        gr.update(visible=False),  # send_btn
                        gr.update(visible=False),  # export_btn
                        gr.update(visible=False),  # download_file
                        []  # chat_state
                    )
                # 2. In on_analyze, update df_rows to exclude candidate name
                def on_analyze(jd_name):
                    import gradio as gr
                    # Disable interactive elements and show progress bar immediately
                    processing_html = '<div class="flashing-red">🔄 Processing... Please wait</div>'
                    disable_tabs_html = '<script>document.dispatchEvent(new Event("processing-start"));</script>'
                    yield gr.update(visible=False, value=[]), [], gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(value=processing_html, visible=True), gr.update(value=disable_tabs_html, visible=True)
                    if not jd_name or jd_name == "No job descriptions available":
                        enable_tabs_html = '<script>document.dispatchEvent(new Event("processing-end"));</script>'
                        yield gr.update(visible=False, value=[]), [], gr.update(interactive=True), gr.update(interactive=True), gr.update(visible=True), gr.update(value='', visible=False), gr.update(value=enable_tabs_html, visible=True)
                        return
                    total = 0
                    for _ in ui_manager.analyze_jd(jd_name):
                        total += 1
                    processed = 0
                    for table_html, summary_html, download_content, progress_msg, detail_buttons in ui_manager.analyze_jd(jd_name):
                        processed += 1
                        df_rows = []
                        for idx, btn in enumerate(detail_buttons):
                            match = "✅ YES" if btn['match'] else "❌ NO"
                            df_rows.append([btn['resume'], match, "🔍 Analysis", "▶ Generate"])
                        # Progress bar: 10 chars, filled for processed, empty for remaining
                        bar_len = 10
                        filled = int(bar_len * processed / total) if total else 0
                        bar = '[' + '#' * filled + '-' * (bar_len - filled) + ']'
                        status_msg = f"Processing {processed}/{total} {bar}" if processed < total else ""
                        processing_html = f'<div class="flashing-red">🔄 {status_msg}</div>'
                        yield gr.update(visible=True, value=df_rows), detail_buttons, gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=True), gr.update(value=processing_html, visible=True), gr.update(visible=False)
                    enable_tabs_html = '<script>document.dispatchEvent(new Event("processing-end"));</script>'
                    yield gr.update(visible=True, value=df_rows), detail_buttons, gr.update(interactive=True), gr.update(interactive=True), gr.update(visible=True), gr.update(value='', visible=False), gr.update(value=enable_tabs_html, visible=True)

                def on_row_action(evt: gr.SelectData, df, details, jd_name):
                    if isinstance(evt.index, (list, tuple)) and len(evt.index) == 2:
                        row_idx, col_idx = evt.index
                    else:
                        row_idx = evt.index
                        col_idx = None
                    print(f"Row action: row_idx={row_idx}, col_idx={col_idx}, details={details}")
                    if not details or row_idx is None or row_idx >= len(details):
                        return (
                            gr.update(value="No details available.", visible=True),
                            gr.update(value="## Views"),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            []
                        )
                    btn = details[row_idx]
                    if col_idx == 2:  # 'Analysis' column (now index 2 after removing Candidate Name)
                        header = f"## {btn.get('candidate', 'Candidate')} match to {jd_name} selected"
                        summary_md = btn['summary']  # Markdown text
                        return (
                            gr.update(value=summary_md, visible=True),
                            gr.update(value=header),
                            gr.update(visible=False),  # chatbox
                            gr.update(visible=False),  # user_question
                            gr.update(visible=False),  # send_btn
                            gr.update(visible=False),  # export_btn
                            gr.update(visible=False),  # download_file
                            []
                        )
                    elif col_idx == 3:  # 'Interview Questions' column (now index 3)
                        jd_content = ui_manager.get_jd_content(jd_name)
                        import asyncio
                        async def get_questions():
                            try:
                                output_text = await ui_manager.analyzer.generate_interview_questions(jd_content)
                                return output_text
                            except Exception as e:
                                return f"Error generating interview questions: {e}"
                        output_text = asyncio.run(get_questions())
                        chat_init = [
                            {"role": "assistant", "content": output_text}
                        ]
                        return (
                            gr.update(value="", visible=False),
                            gr.update(value=f"## Interview Questions: {btn['resume']}"),
                            gr.update(value=chat_init, visible=True),
                            gr.update(visible=True, value=""),
                            gr.update(visible=True),
                            gr.update(visible=True),  # export_btn
                            gr.update(visible=False), # download_file
                            chat_init
                        )
                    else:
                        # Ignore clicks on all other columns
                        return (
                            gr.update(value="No details available.", visible=True),
                            gr.update(value="## Views"),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            []
                        )
                def on_generate_questions(selected, details):
                    import gradio as gr
                    import asyncio
                    if not details or not selected:
                        return gr.update(value="<div>No details available.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    resume_name = selected.split(' (')[0]
                    btn = None
                    for d in details:
                        if d['resume'] == resume_name:
                            btn = d
                            break
                    if not btn:
                        return gr.update(value="<div>No details available.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    jd_name = jd_dropdown.value
                    jd_content = ui_manager.get_jd_content(jd_name)
                    if not jd_content:
                        return gr.update(value="<div>Could not load job description.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    async def get_questions():
                        try:
                            output_text = await ui_manager.analyzer.generate_interview_questions(jd_content)
                            return output_text
                        except Exception as e:
                            return f"Error generating interview questions: {e}"
                    output_text = asyncio.run(get_questions())
                    chat_history = [
                        {"role": "assistant", "content": output_text}
                    ]
                    return (
                        gr.update(visible=False),
                        gr.update(visible=True, value=chat_history),
                        gr.update(visible=True, value=""),
                        gr.update(visible=True),
                        gr.update(visible=True),
                        chat_history,
                        gr.update(value="Interview Questions")
                    )
                def on_user_question(chat_history, user_input, jd_name, details):
                    import gradio as gr
                    import asyncio
                    if not user_input.strip():
                        return gr.update(), chat_history
                    # Use the last selected candidate from details (if available)
                    btn = details[-1] if details else None
                    jd_content = ui_manager.get_jd_content(jd_name)
                    resume_content = ui_manager.cache_manager.get_resume_content(btn['resume']) if btn else ""
                    # Compose context for follow-up
                    context = f"Job Description:\n{jd_content}\n\nResume:\n{resume_content}\n\nPrevious Q&A:\n"
                    for msg in chat_history:
                        if msg["role"] == "user":
                            context += f"Q: {msg['content']}\n"
                        elif msg["role"] == "assistant":
                            context += f"A: {msg['content']}\n"
                    prompt = f"{context}\nUser follow-up question: {user_input}\nPlease answer as an expert interviewer."
                    async def get_response():
                        try:
                            agent_result = await ui_manager.analyzer.run(prompt, model=ui_manager.model)
                            if hasattr(agent_result, 'output'):
                                output_text = agent_result.output
                            else:
                                output_text = str(agent_result)
                            return output_text
                        except Exception as e:
                            return f"Error: {e}"
                    output_text = asyncio.run(get_response())
                    chat_history = chat_history + [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": output_text}
                    ]
                    return gr.update(value=chat_history), chat_history
                def on_export_chat(chat_history):
                    import tempfile
                    chat_text = ""
                    for msg in chat_history:
                        chat_text += f"{msg['role'].capitalize()}: {msg['content']}\n\n"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
                        f.write(chat_text)
                        file_path = f.name
                    return gr.update(value=file_path, visible=True)
                def on_export_data(selected, details):
                    # For now, show 'not implemented' in the Interview Questions output
                    return gr.update(value="not implemented")
                # Connect events
                jd_dropdown.change(
                    fn=on_jd_select,
                    inputs=[jd_dropdown],
                    outputs=[right_view_md, right_header, analyze_btn, results_df, details_state, analyze_tip, chatbox, user_question, send_btn, export_btn, download_file, chat_state]
                )
                analyze_btn.click(
                    fn=on_analyze,
                    inputs=[jd_dropdown],
                    outputs=[results_df, details_state, analyze_btn, jd_dropdown, analyze_tip, analyze_status, tab_control_trigger]
                )
                results_df.select(
                    fn=on_row_action,
                    inputs=[results_df, details_state, jd_dropdown],
                    outputs=[right_view_md, right_header, chatbox, user_question, send_btn, export_btn, download_file, chat_state]
                )
                send_btn.click(
                    fn=on_user_question,
                    inputs=[chat_state, user_question, jd_dropdown, details_state],
                    outputs=[chatbox, chat_state]
                )
                export_btn.click(
                    fn=on_export_chat,
                    inputs=[chat_state],
                    outputs=[download_file]
                )
            
            # New "Screen by Candidate" tab
            with gr.TabItem("Screen by Candidate"):
                with gr.Row():
                    # Left Panel
                    with gr.Column(scale=1):
                        gr.Markdown("## Candidate Selection")
                        with gr.Row():
                            candidate_dropdown = gr.Dropdown(
                                choices=ui_manager.cache_manager.get_available_resumes(),
                                label="Select Candidate",
                                interactive=True,
                                value=ui_manager.cache_manager.get_available_resumes()[0] if ui_manager.cache_manager.get_available_resumes() else None
                            )
                        
                        gr.Markdown("## Job Description Selection")
                        with gr.Row():
                            jd_multiselect = gr.Dropdown(
                                choices=ui_manager.get_available_jds(),
                                label="Select JDs (Optional - Leave empty to analyze against all JDs)",
                                interactive=True,
                                multiselect=True,
                                value=None
                            )
                        
                        # Dynamic Analyze button label for candidate
                        def get_analyze_candidate_label(candidate_name, selected_jds):
                            if candidate_name and candidate_name != "No candidates available":
                                if selected_jds and len(selected_jds) > 0:
                                    if len(selected_jds) == 1:
                                        return f"Analyze {candidate_name} for {selected_jds[0]}"
                                    else:
                                        return f"Analyze {candidate_name} for {len(selected_jds)} JDs"
                                else:
                                    return f"Analyze {candidate_name} for All JDs"
                            return "Analyze"
                        
                        analyze_candidate_btn = gr.Button(get_analyze_candidate_label(candidate_dropdown.value, []), variant="primary")
                        analyze_candidate_tip = gr.Markdown("**Tip:** Click the '🔍 Analysis' or '▶ Generate' cell in the table below to see details in the right pane.", visible=False)
                        candidate_results_df = gr.Dataframe(
                            headers=["Job Description", "Match", "Analysis", "Interview Questions"],
                            interactive=False,
                            datatype=["str", "str", "str", "str"],
                            visible=False
                        )
                        candidate_details_state = gr.State([])  # To store detail_buttons data
                        analyze_candidate_status = gr.HTML("", visible=False, elem_classes=["flashing-red"])
                        # JavaScript trigger for tab control
                        candidate_tab_control_trigger = gr.HTML("", visible=False)
                    
                    # Right Panel
                    with gr.Column(scale=1):
                        if candidate_dropdown.value:
                            default_candidate_content = ui_manager.cache_manager.get_resume_content(candidate_dropdown.value)
                            candidate_right_header = gr.Markdown(f"## Candidate: {candidate_dropdown.value}")
                            candidate_right_view_md = gr.Markdown(
                                value=f"<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'><pre style='white-space: pre-wrap; margin:0;'>{default_candidate_content}</pre></div>",
                                visible=True
                            )
                            candidate_chatbox = gr.Chatbot(label="Interview Questions Chat", visible=False, elem_id="candidate-interview-questions-chat", type="messages")
                            candidate_user_question = gr.Textbox(label="Ask a question about the interview questions", visible=False, placeholder="Type your question and press Enter...")
                            candidate_send_btn = gr.Button("Send", visible=False)
                            candidate_chat_state = gr.State([])
                            candidate_export_btn = gr.Button("Export", visible=False)
                            candidate_download_file = gr.File(label="Download Chat", visible=False)
                        else:
                            candidate_right_header = gr.Markdown("## Views")
                            candidate_right_view_md = gr.Markdown(
                                value="<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'>No candidate selected.</div>",
                                visible=True
                            )
                            candidate_chatbox = gr.Chatbot(label="Interview Questions Chat", visible=False, elem_id="candidate-interview-questions-chat", type="messages")
                            candidate_user_question = gr.Textbox(label="Ask a question about the interview questions", visible=False, placeholder="Type your question and press Enter...")
                            candidate_send_btn = gr.Button("Send", visible=False)
                            candidate_chat_state = gr.State([])
                            candidate_export_btn = gr.Button("Export", visible=False)
                            candidate_download_file = gr.File(label="Download Chat", visible=False)
                
                # Event handlers for candidate tab
                def on_candidate_select(candidate_name, selected_jds=None):
                    if selected_jds is None:
                        selected_jds = []
                    if candidate_name and candidate_name != "No candidates available":
                        content = ui_manager.cache_manager.get_resume_content(candidate_name)
                        html_box = f"<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'><pre style='white-space: pre-wrap; margin:0;'>{content}</pre></div>"
                        return (
                            gr.update(value=html_box, visible=True),
                            gr.update(value=f"## Candidate: {candidate_name}"),
                            gr.update(value=get_analyze_candidate_label(candidate_name, selected_jds)),
                            gr.update(value=[], visible=False),  # candidate_results_df
                            [],  # candidate_details_state
                            gr.update(visible=False),  # analyze_candidate_tip
                            gr.update(value=[], visible=False),  # candidate_chatbox
                            gr.update(value="", visible=False),  # candidate_user_question
                            gr.update(visible=False),  # candidate_send_btn
                            gr.update(visible=False),  # candidate_export_btn
                            gr.update(visible=False),  # candidate_download_file
                            []  # candidate_chat_state
                        )
                    return (
                        gr.update(value="<div style='max-height:500px; min-height:300px; max-width:100%; overflow:auto; border:1px solid #ddd; border-radius:6px; padding:16px; background:#fafbfc;'>No candidate selected.</div>", visible=True),
                        gr.update(value="## Views"),
                        gr.update(value="Analyze"),
                        gr.update(value=[], visible=False),  # candidate_results_df
                        [],  # candidate_details_state
                        gr.update(visible=False),  # analyze_candidate_tip
                        gr.update(value=[], visible=False),  # candidate_chatbox
                        gr.update(value="", visible=False),  # candidate_user_question
                        gr.update(visible=False),  # candidate_send_btn
                        gr.update(visible=False),  # candidate_export_btn
                        gr.update(visible=False),  # candidate_download_file
                        []  # candidate_chat_state
                    )
                
                def on_jd_multiselect_change(candidate_name, selected_jds):
                    if selected_jds is None:
                        selected_jds = []
                    return gr.update(value=get_analyze_candidate_label(candidate_name, selected_jds))
                
                def on_analyze_candidate(candidate_name, selected_jds=None):
                    import gradio as gr
                    import asyncio
                    # Disable interactive elements and show progress bar immediately
                    processing_html = '<div class="flashing-red">🔄 Processing... Please wait</div>'
                    disable_tabs_html = '<script>document.dispatchEvent(new Event("processing-start"));</script>'
                    yield gr.update(visible=False, value=[]), [], gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=False), gr.update(value=processing_html, visible=True), gr.update(value=disable_tabs_html, visible=True)
                    
                    if not candidate_name or candidate_name == "No candidates available":
                        enable_tabs_html = '<script>document.dispatchEvent(new Event("processing-end"));</script>'
                        yield gr.update(visible=False, value=[]), [], gr.update(interactive=True), gr.update(interactive=True), gr.update(visible=True), gr.update(value='', visible=False), gr.update(value=enable_tabs_html, visible=True)
                        return
                    
                    # Get JDs to analyze against
                    if selected_jds and len(selected_jds) > 0:
                        # Use selected JDs
                        jds_to_analyze = selected_jds
                    else:
                        # Use all available JDs
                        available_jds = ui_manager.get_available_jds()
                        jds_to_analyze = [jd for jd in available_jds if jd != "No job descriptions available"]
                    
                    if not jds_to_analyze:
                        enable_tabs_html = '<script>document.dispatchEvent(new Event("processing-end"));</script>'
                        yield gr.update(visible=False, value=[]), [], gr.update(interactive=True), gr.update(interactive=True), gr.update(visible=True), gr.update(value='', visible=False), gr.update(value=enable_tabs_html, visible=True)
                        return
                    
                    # Analyze candidate against selected/all JDs
                    results = []
                    detail_buttons = []
                    total_jds = len(jds_to_analyze)
                    processed = 0
                    
                    for jd_name in jds_to_analyze:
                        try:
                            jd_content = ui_manager.get_jd_content(jd_name)
                            resume_content = ui_manager.cache_manager.get_resume_content(candidate_name)
                            result = asyncio.run(ui_manager.analyzer.analyze_resume(jd_content, resume_content))
                            
                            # Format result for table display
                            results.append([
                                jd_name,
                                "✅ YES" if result.match else "❌ NO",
                                "🔍 Analysis",
                                "▶ Generate"
                            ])
                            
                            # Create detail button data
                            detail_buttons.append({
                                'jd_name': jd_name,
                                'candidate': candidate_name,
                                'match': result.match,
                                'summary': result.summary,
                                'full_analysis': result.summary
                            })
                            
                            processed += 1
                            # Progress bar: 10 chars, filled for processed, empty for remaining
                            bar_len = 10
                            filled = int(bar_len * processed / total_jds) if total_jds else 0
                            bar = '[' + '#' * filled + '-' * (bar_len - filled) + ']'
                            status_msg = f"Processing {processed}/{total_jds} {bar}" if processed < total_jds else ""
                            processing_html = f'<div class="flashing-red">🔄 {status_msg}</div>'
                            yield gr.update(visible=True, value=results), detail_buttons, gr.update(interactive=False), gr.update(interactive=False), gr.update(visible=True), gr.update(value=processing_html, visible=True), gr.update(visible=False)
                            
                        except Exception as e:
                            results.append([
                                jd_name,
                                "❌ ERROR",
                                "🔍 Analysis",
                                "▶ Generate"
                            ])
                            detail_buttons.append({
                                'jd_name': jd_name,
                                'candidate': candidate_name,
                                'match': False,
                                'summary': f"Error: {str(e)}",
                                'full_analysis': f"Error: {str(e)}"
                            })
                            processed += 1
                    
                    enable_tabs_html = '<script>document.dispatchEvent(new Event("processing-end"));</script>'
                    yield gr.update(visible=True, value=results), detail_buttons, gr.update(interactive=True), gr.update(interactive=True), gr.update(visible=True), gr.update(value='', visible=False), gr.update(value=enable_tabs_html, visible=True)
                
                def on_candidate_row_action(evt: gr.SelectData, df, details, candidate_name):
                    if isinstance(evt.index, (list, tuple)) and len(evt.index) == 2:
                        row_idx, col_idx = evt.index
                    else:
                        row_idx = evt.index
                        col_idx = None
                    print(f"Candidate row action: row_idx={row_idx}, col_idx={col_idx}, details={details}")
                    
                    if not details or row_idx is None or row_idx >= len(details):
                        return (
                            gr.update(value="No details available.", visible=True),
                            gr.update(value="## Views"),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            []
                        )
                    
                    btn = details[row_idx]
                    jd_name = btn.get('jd_name', 'Unknown JD')
                    
                    if col_idx == 2:  # 'Analysis' column
                        header = f"## {candidate_name} match to {jd_name}"
                        summary_md = btn['summary']  # Markdown text
                        return (
                            gr.update(value=summary_md, visible=True),
                            gr.update(value=header),
                            gr.update(visible=False),  # candidate_chatbox
                            gr.update(visible=False),  # candidate_user_question
                            gr.update(visible=False),  # candidate_send_btn
                            gr.update(visible=False),  # candidate_export_btn
                            gr.update(visible=False),  # candidate_download_file
                            []
                        )
                    elif col_idx == 3:  # 'Interview Questions' column
                        jd_content = ui_manager.get_jd_content(jd_name)
                        import asyncio
                        async def get_questions():
                            try:
                                output_text = await ui_manager.analyzer.generate_interview_questions(jd_content)
                                return output_text
                            except Exception as e:
                                return f"Error generating interview questions: {e}"
                        output_text = asyncio.run(get_questions())
                        chat_init = [
                            {"role": "assistant", "content": output_text}
                        ]
                        return (
                            gr.update(value="", visible=False),
                            gr.update(value=f"## Interview Questions: {candidate_name} for {jd_name}"),
                            gr.update(value=chat_init, visible=True),
                            gr.update(visible=True, value=""),
                            gr.update(visible=True),
                            gr.update(visible=True),  # candidate_export_btn
                            gr.update(visible=False), # candidate_download_file
                            chat_init
                        )
                    else:
                        # Ignore clicks on all other columns
                        return (
                            gr.update(value="No details available.", visible=True),
                            gr.update(value="## Views"),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            []
                        )
                def on_generate_questions(selected, details):
                    import gradio as gr
                    import asyncio
                    if not details or not selected:
                        return gr.update(value="<div>No details available.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    resume_name = selected.split(' (')[0]
                    btn = None
                    for d in details:
                        if d['resume'] == resume_name:
                            btn = d
                            break
                    if not btn:
                        return gr.update(value="<div>No details available.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    jd_name = jd_dropdown.value
                    jd_content = ui_manager.get_jd_content(jd_name)
                    if not jd_content:
                        return gr.update(value="<div>Could not load job description.</div>"), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], gr.update(value="Interview Questions")
                    async def get_questions():
                        try:
                            output_text = await ui_manager.analyzer.generate_interview_questions(jd_content)
                            return output_text
                        except Exception as e:
                            return f"Error generating interview questions: {e}"
                    output_text = asyncio.run(get_questions())
                    chat_history = [
                        {"role": "assistant", "content": output_text}
                    ]
                    return (
                        gr.update(visible=False),
                        gr.update(visible=True, value=chat_history),
                        gr.update(visible=True, value=""),
                        gr.update(visible=True),
                        gr.update(visible=True),
                        chat_history,
                        gr.update(value="Interview Questions")
                    )
                def on_user_question(chat_history, user_input, jd_name, details):
                    import gradio as gr
                    import asyncio
                    if not user_input.strip():
                        return gr.update(), chat_history
                    # Use the last selected candidate from details (if available)
                    btn = details[-1] if details else None
                    jd_content = ui_manager.get_jd_content(jd_name)
                    resume_content = ui_manager.cache_manager.get_resume_content(btn['resume']) if btn else ""
                    # Compose context for follow-up
                    context = f"Job Description:\n{jd_content}\n\nResume:\n{resume_content}\n\nPrevious Q&A:\n"
                    for msg in chat_history:
                        if msg["role"] == "user":
                            context += f"Q: {msg['content']}\n"
                        elif msg["role"] == "assistant":
                            context += f"A: {msg['content']}\n"
                    prompt = f"{context}\nUser follow-up question: {user_input}\nPlease answer as an expert interviewer."
                    async def get_response():
                        try:
                            agent_result = await ui_manager.analyzer.run(prompt, model=ui_manager.model)
                            if hasattr(agent_result, 'output'):
                                output_text = agent_result.output
                            else:
                                output_text = str(agent_result)
                            return output_text
                        except Exception as e:
                            return f"Error: {e}"
                    output_text = asyncio.run(get_response())
                    chat_history = chat_history + [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": output_text}
                    ]
                    return gr.update(value=chat_history), chat_history
                def on_export_chat(chat_history):
                    import tempfile
                    chat_text = ""
                    for msg in chat_history:
                        chat_text += f"{msg['role'].capitalize()}: {msg['content']}\n\n"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
                        f.write(chat_text)
                        file_path = f.name
                    return gr.update(value=file_path, visible=True)
                def on_export_data(selected, details):
                    # For now, show 'not implemented' in the Interview Questions output
                    return gr.update(value="not implemented")
                
                # Helper functions for candidate tab
                def on_candidate_user_question(chat_history, user_input, candidate_name, details):
                    import gradio as gr
                    import asyncio
                    if not user_input.strip():
                        return gr.update(), chat_history
                    # Use the last selected JD from details (if available)
                    btn = details[-1] if details else None
                    jd_name = btn.get('jd_name', '') if btn else ""
                    jd_content = ui_manager.get_jd_content(jd_name) if jd_name else ""
                    resume_content = ui_manager.cache_manager.get_resume_content(candidate_name) if candidate_name else ""
                    # Compose context for follow-up
                    context = f"Job Description:\n{jd_content}\n\nResume:\n{resume_content}\n\nPrevious Q&A:\n"
                    for msg in chat_history:
                        if msg["role"] == "user":
                            context += f"Q: {msg['content']}\n"
                        elif msg["role"] == "assistant":
                            context += f"A: {msg['content']}\n"
                    prompt = f"{context}\nUser follow-up question: {user_input}\nPlease answer as an expert interviewer."
                    async def get_response():
                        try:
                            agent_result = await ui_manager.analyzer.run(prompt, model=ui_manager.model)
                            if hasattr(agent_result, 'output'):
                                output_text = agent_result.output
                            else:
                                output_text = str(agent_result)
                            return output_text
                        except Exception as e:
                            return f"Error: {e}"
                    output_text = asyncio.run(get_response())
                    chat_history = chat_history + [
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": output_text}
                    ]
                    return gr.update(value=chat_history), chat_history
                 
                def on_candidate_export_chat(chat_history):
                    import tempfile
                    chat_text = ""
                    for msg in chat_history:
                        chat_text += f"{msg['role'].capitalize()}: {msg['content']}\n\n"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
                        f.write(chat_text)
                        file_path = f.name
                    return gr.update(value=file_path, visible=True)
                
                # Connect events for candidate tab
                candidate_dropdown.change(
                    fn=on_candidate_select,
                    inputs=[candidate_dropdown, jd_multiselect],
                    outputs=[candidate_right_view_md, candidate_right_header, analyze_candidate_btn, candidate_results_df, candidate_details_state, analyze_candidate_tip, candidate_chatbox, candidate_user_question, candidate_send_btn, candidate_export_btn, candidate_download_file, candidate_chat_state]
                )
                jd_multiselect.change(
                    fn=on_jd_multiselect_change,
                    inputs=[candidate_dropdown, jd_multiselect],
                    outputs=[analyze_candidate_btn]
                )
                analyze_candidate_btn.click(
                    fn=on_analyze_candidate,
                    inputs=[candidate_dropdown, jd_multiselect],
                    outputs=[candidate_results_df, candidate_details_state, analyze_candidate_btn, candidate_dropdown, analyze_candidate_tip, analyze_candidate_status, candidate_tab_control_trigger]
                )
                candidate_results_df.select(
                    fn=on_candidate_row_action,
                    inputs=[candidate_results_df, candidate_details_state, candidate_dropdown],
                    outputs=[candidate_right_view_md, candidate_right_header, candidate_chatbox, candidate_user_question, candidate_send_btn, candidate_export_btn, candidate_download_file, candidate_chat_state]
                )
                candidate_send_btn.click(
                    fn=on_candidate_user_question,
                    inputs=[candidate_chat_state, candidate_user_question, candidate_dropdown, candidate_details_state],
                    outputs=[candidate_chatbox, candidate_chat_state]
                )
                candidate_export_btn.click(
                    fn=on_candidate_export_chat,
                    inputs=[candidate_chat_state],
                    outputs=[candidate_download_file]
                )
            
            with gr.TabItem("Admin"):
                gr.Markdown("## Admin: Upload Job Descriptions and Resumes")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Upload Job Descriptions (PDF/TXT)")
                        jd_upload = gr.File(file_types=[".pdf", ".txt"], file_count="multiple", label="Upload JD(s)")
                        upload_jd_btn = gr.Button("Upload JD(s)")
                        jd_upload_status = gr.Markdown("", visible=False)
                        jd_file_list = gr.Markdown("", visible=True)
                    with gr.Column():
                        gr.Markdown("### Upload Resumes (PDF/TXT)")
                        resume_upload = gr.File(file_types=[".pdf", ".txt"], file_count="multiple", label="Upload Resume(s)")
                        upload_resume_btn = gr.Button("Upload Resume(s)")
                        resume_upload_status = gr.Markdown("", visible=False)
                        resume_file_list = gr.Markdown("", visible=True)

                def list_files(folder):
                    files = sorted([f for f in os.listdir(folder) if f.endswith('.pdf') or f.endswith('.txt')])
                    if not files:
                        return "_No files found._"
                    return "\n".join(f"- {f}" for f in files)

                def handle_upload(files, folder, cache_manager):
                    import shutil
                    if not files:
                        return gr.update(value="No files selected.", visible=True), gr.update(value=list_files(folder), visible=True)
                    for file in files:
                        dest = os.path.join(folder, os.path.basename(file.name))
                        shutil.copy(file.name, dest)
                    cache_manager.refresh_cache()
                    return gr.update(value=f"Uploaded {len(files)} file(s) successfully.", visible=True), gr.update(value=list_files(folder), visible=True)

                upload_jd_btn.click(
                    fn=lambda files: handle_upload(files, ui_manager.jd_folder, ui_manager.cache_manager),
                    inputs=[jd_upload],
                    outputs=[jd_upload_status, jd_file_list]
                )
                upload_resume_btn.click(
                    fn=lambda files: handle_upload(files, ui_manager.resume_folder, ui_manager.cache_manager),
                    inputs=[resume_upload],
                    outputs=[resume_upload_status, resume_file_list]
                )
                # Show file lists on load
                jd_file_list.value = list_files(ui_manager.jd_folder)
                resume_file_list.value = list_files(ui_manager.resume_folder)
    
    return interface

def main():
    """Main function to launch the Gradio interface."""
    interface = create_ui()
    
    if interface:
        print("Starting HR Analyst Agent UI...")
        print("Open your browser and navigate to the URL shown below.")
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False
        )
    else:
        print("Failed to create UI. Please check your configuration.")

if __name__ == "__main__":
    main() 