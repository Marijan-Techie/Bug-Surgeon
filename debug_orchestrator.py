#!/usr/bin/env python3
"""
Claude Code 'Bug Surgeon' - Production Debug Orchestrator
Integrates with GitHub Actions to provide AI-powered debugging assistance
"""

import os
import json
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Third-party imports
try:
    from anthropic import Anthropic
    from github import Github
    from github.Repository import Repository
    from github.Issue import Issue
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install anthropic PyGithub")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BugAnalysis:
    """Results from bug analysis"""
    root_cause: str
    explanation: str
    file_changes: Dict[str, str]
    reasoning_trace: List[str]
    confidence: str


@dataclass
class ToolRequest:
    """Represents a request for file access or other tools"""
    tool: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
        logger.info("Loaded environment variables from .env file")
    else:
        logger.warning("No .env file found")


class BugSurgeon:
    """Main orchestrator for AI-powered debugging"""

    # Expert system prompt - the actual production version
    EXPERT_SYSTEM_PROMPT = """You are a Senior Debugging Specialist with expertise in systematic root cause analysis. Your goal is to identify and resolve the fundamental cause of issues, not merely patch symptoms.

<reasoning_methodology>
1. Analyze the problem context thoroughly before proposing solutions
2. Form hypotheses about potential root causes  
3. Request additional context when needed to validate hypotheses
4. Explain your reasoning process transparently using <thinking> tags
5. Provide solutions that address the underlying issue, not just symptoms
</reasoning_methodology>

<constraints>
- Maintain existing code style and patterns
- Explain the reasoning behind your analysis
- If uncertain, state assumptions clearly and request clarification
- Focus on sustainable fixes over quick patches
- Only suggest changes to files you've actually examined
</constraints>

<tool_usage>
When you need to examine code files, respond with:
TOOL_REQUEST: read_file
FILE: path/to/file.py
START_LINE: 30 (optional)
END_LINE: 50 (optional)

After examining files, provide your analysis and solution.
</tool_usage>

<output_format>
Always use <thinking> tags to externalize your reasoning process, then provide your final analysis and solution.

For your final response, structure it as:
<analysis>
ROOT_CAUSE: Brief description of the root cause
EXPLANATION: Detailed explanation of why this issue occurs
CONFIDENCE: HIGH/MEDIUM/LOW based on available evidence
</analysis>

<solution>
Provide the corrected code with clear explanations
</solution>
</output_format>"""

    # Available models in order of preference
    AVAILABLE_MODELS = [
        "claude-3-5-sonnet-20240620",  # Current stable
        "claude-3-sonnet-20240229",  # Fallback
        "claude-3-haiku-20240307"  # Fast fallback
    ]

    def __init__(self):
        """Initialize the Bug Surgeon with API clients"""
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        try:
            # Try with explicit parameters to avoid proxy issues
            self.claude = Anthropic(
                api_key=api_key,
                max_retries=3,
                timeout=60.0
            )
            logger.info("Anthropic client initialized successfully")
        except TypeError as e:
            if "proxies" in str(e):
                # Fallback for version compatibility issues
                try:
                    self.claude = Anthropic(api_key=api_key)
                    logger.info("Anthropic client initialized with fallback method")
                except Exception:
                    # Last resort - try with minimal parameters
                    import anthropic
                    self.claude = anthropic.Client(api_key=api_key)
                    logger.info("Anthropic client initialized with minimal parameters")
            else:
                raise e

        # Test which model works
        self.working_model = self._find_working_model()

        # Initialize GitHub client (make it optional for local testing)
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token and github_token != 'dummy_token_for_local_test':
            try:
                self.github = Github(github_token)
                logger.info("GitHub client initialized successfully")
            except Exception as e:
                logger.warning(f"GitHub initialization failed: {e}")
                self.github = None
        else:
            logger.info("GitHub token not provided - running in local mode")
            self.github = None

        # Get repository context (optional)
        repo_name = os.getenv('GITHUB_REPOSITORY')
        if repo_name and self.github:
            try:
                self.repo = self.github.get_repo(repo_name)
                logger.info(f"Connected to repository: {self.repo.full_name}")
            except Exception as e:
                logger.warning(f"Could not connect to repository {repo_name}: {e}")
                self.repo = None
        else:
            self.repo = None
            if not repo_name:
                logger.info("GITHUB_REPOSITORY not set - running in local mode")
            else:
                logger.info("GitHub client not available - running in local mode")

    def _find_working_model(self) -> str:
        """Find a working Claude model"""
        for model in self.AVAILABLE_MODELS:
            try:
                # Test the model with a simple call
                response = self.claude.messages.create(
                    model=model,
                    max_tokens=10,
                    system="You are helpful.",
                    messages=[{"role": "user", "content": "Hi"}]
                )
                logger.info(f"Using model: {model}")
                return model
            except Exception as e:
                logger.warning(f"Model {model} not available: {e}")
                continue

        # If no models work, default to the first one and let it fail gracefully
        logger.error("No working models found, using default")
        return self.AVAILABLE_MODELS[0]

    def read_file_content(self, file_path: str, start_line: Optional[int] = None,
                          end_line: Optional[int] = None) -> str:
        """Read file content from repository or local filesystem"""
        try:
            if self.repo:
                # GitHub Actions mode - read from repository
                try:
                    file_content = self.repo.get_contents(file_path)
                    content = file_content.decoded_content.decode('utf-8')
                except Exception as e:
                    logger.error(f"Failed to read {file_path} from repo: {e}")
                    return f"Error reading file: {e}"
            else:
                # Local mode - read from filesystem
                local_path = Path(file_path)
                if not local_path.exists():
                    return f"File not found: {file_path}"
                content = local_path.read_text(encoding='utf-8')

            # Extract specific lines if requested
            if start_line or end_line:
                lines = content.split('\n')
                start = (start_line - 1) if start_line else 0
                end = end_line if end_line else len(lines)
                content = '\n'.join(lines[start:end])
                return f"# {file_path} lines {start + 1}-{end}\n{content}"

            return f"# {file_path}\n{content}"

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"

    def analyze_bug_direct(self, issue_description: str, file_paths: List[str] = None) -> Optional[BugAnalysis]:
        """Direct analysis method - provides file content upfront to avoid ReAct loops"""
        logger.info("Starting direct bug analysis...")

        # Build comprehensive prompt with file contents if provided
        comprehensive_prompt = f"""
{issue_description}

Please analyze this systematically and identify the root cause.
"""

        # Add file contents if file paths are provided
        if file_paths:
            comprehensive_prompt += "\n\nRelevant file contents:\n"
            for file_path in file_paths:
                file_content = self.read_file_content(file_path)
                if "Error reading file" not in file_content:
                    comprehensive_prompt += f"\n```python\n{file_content}\n```\n"
                    logger.info(f"Added content for {file_path}")
                else:
                    logger.warning(f"Could not read {file_path}")

        comprehensive_prompt += """
Provide your analysis in this format:
<analysis>
ROOT_CAUSE: Brief description of the root cause
EXPLANATION: Detailed explanation of why this issue occurs
CONFIDENCE: HIGH/MEDIUM/LOW based on available evidence
</analysis>

<solution>
Provide the corrected code with clear explanations
</solution>
"""

        try:
            response = self.claude.messages.create(
                model=self.working_model,
                max_tokens=4096,
                system=self.EXPERT_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": comprehensive_prompt}
                ],
                temperature=0.1
            )

            response_text = response.content[0].text
            logger.info(f"Claude response length: {len(response_text)} chars")

            # Extract analysis
            analysis = self.extract_analysis(response_text)
            if analysis:
                analysis.reasoning_trace = [f"Direct analysis: {response_text[:200]}..."]
                logger.info("Direct bug analysis completed successfully")
                return analysis
            else:
                # Create fallback analysis
                logger.warning("No structured analysis found, creating from response")
                return self._create_fallback_analysis(response_text)

        except Exception as e:
            logger.error(f"Error in direct analysis: {e}")
            return None

    def parse_tool_requests(self, response_text: str) -> List[ToolRequest]:
        """Parse tool requests from Claude's response"""
        tool_requests = []
        lines = response_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('TOOL_REQUEST:'):
                try:
                    tool_type = line.split(':', 1)[1].strip()
                    file_path = None
                    start_line = None
                    end_line = None

                    # Look for file path in next few lines
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line.startswith('FILE:'):
                            file_path = next_line.split(':', 1)[1].strip()
                        elif next_line.startswith('START_LINE:'):
                            try:
                                start_line = int(next_line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif next_line.startswith('END_LINE:'):
                            try:
                                end_line = int(next_line.split(':', 1)[1].strip())
                            except ValueError:
                                pass

                    if file_path:
                        tool_requests.append(ToolRequest(
                            tool=tool_type,
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line
                        ))

                except Exception as e:
                    logger.error(f"Error parsing tool request: {e}")

            i += 1

        return tool_requests

    def extract_analysis(self, response_text: str) -> Optional[BugAnalysis]:
        """Extract structured analysis from Claude's response"""
        try:
            # Extract analysis block
            analysis_match = re.search(r'<analysis>(.*?)</analysis>', response_text, re.DOTALL)
            if not analysis_match:
                logger.warning("No analysis block found in response")
                return self._create_fallback_analysis(response_text)

            analysis_text = analysis_match.group(1)

            # Parse analysis components
            root_cause = ""
            explanation = ""
            confidence = "MEDIUM"

            for line in analysis_text.split('\n'):
                line = line.strip()
                if line.startswith('ROOT_CAUSE:'):
                    root_cause = line.split(':', 1)[1].strip()
                elif line.startswith('EXPLANATION:'):
                    explanation = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    confidence = line.split(':', 1)[1].strip()

            # Extract solution block
            solution_match = re.search(r'<solution>(.*?)</solution>', response_text, re.DOTALL)
            solution_text = solution_match.group(1) if solution_match else ""

            # Extract thinking traces
            thinking_matches = re.findall(r'<thinking>(.*?)</thinking>', response_text, re.DOTALL)
            reasoning_trace = [match.strip() for match in thinking_matches]

            return BugAnalysis(
                root_cause=root_cause or "Analysis completed",
                explanation=explanation or response_text[:500] + "...",
                file_changes={"solution.md": solution_text},
                reasoning_trace=reasoning_trace,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error extracting analysis: {e}")
            return self._create_fallback_analysis(response_text)

    def _create_fallback_analysis(self, response_text: str) -> BugAnalysis:
        """Create a fallback analysis when structured extraction fails"""
        # Try to extract thinking content
        thinking_matches = re.findall(r'<thinking>(.*?)</thinking>', response_text, re.DOTALL)
        reasoning_trace = [match.strip() for match in thinking_matches]

        # Extract first few sentences as root cause
        sentences = response_text.split('.')
        root_cause = sentences[0] if sentences else "Analysis provided"

        return BugAnalysis(
            root_cause=root_cause[:200] + "..." if len(root_cause) > 200 else root_cause,
            explanation=response_text[:500] + "..." if len(response_text) > 500 else response_text,
            file_changes={"analysis.md": response_text},
            reasoning_trace=reasoning_trace,
            confidence="MEDIUM"
        )

    def analyze_bug(self, issue_description: str, max_iterations: int = 3) -> Optional[BugAnalysis]:
        """Main bug analysis method with fallback to direct analysis"""
        logger.info("Starting bug analysis...")

        # First try to extract file paths mentioned in the issue
        mentioned_files = self._extract_file_paths(issue_description)

        # If we can identify specific files, use direct analysis
        if mentioned_files:
            logger.info(f"Found mentioned files: {mentioned_files}, using direct analysis")
            return self.analyze_bug_direct(issue_description, mentioned_files)

        # Otherwise try ReAct approach with limited iterations
        logger.info("No specific files found, trying ReAct approach")
        return self._analyze_bug_react(issue_description, max_iterations)

    def _extract_file_paths(self, issue_description: str) -> List[str]:
        """Extract file paths mentioned in issue description"""
        # Look for common file path patterns
        import re
        file_patterns = [
            r'File "([^"]+\.py)"',  # File "path/to/file.py"
            r'in ([a-zA-Z_][a-zA-Z0-9_/]*\.py)',  # in auth.py
            r'([a-zA-Z_][a-zA-Z0-9_/]*\.py)',  # direct mention like auth.py
        ]

        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, issue_description)
            files.extend(matches)

        # Filter to files that actually exist
        existing_files = []
        for file_path in files:
            if Path(file_path).exists():
                existing_files.append(file_path)

        return existing_files

    def _analyze_bug_react(self, issue_description: str, max_iterations: int = 3) -> Optional[BugAnalysis]:
        """ReAct analysis method (with improved loop handling)"""
        messages = [
            {"role": "user",
             "content": f"Please analyze this bug report and identify the root cause:\n\n{issue_description}"}
        ]

        iteration = 0
        reasoning_trace = []
        requested_files = set()  # Track requested files to avoid loops

        while iteration < max_iterations:
            try:
                logger.info(f"ReAct iteration {iteration + 1}")

                response = self.claude.messages.create(
                    model=self.working_model,
                    max_tokens=4096,
                    system=self.EXPERT_SYSTEM_PROMPT,
                    messages=messages,
                    temperature=0.1
                )

                response_text = response.content[0].text
                reasoning_trace.append(f"Iteration {iteration + 1}: {response_text[:200]}...")

                # Check for tool requests
                tool_requests = self.parse_tool_requests(response_text)

                if tool_requests:
                    # Add Claude's response to conversation
                    messages.append({"role": "assistant", "content": response_text})

                    # Process tool requests (but avoid duplicate requests)
                    new_files_added = False
                    for tool_request in tool_requests:
                        if tool_request.tool == "read_file" and tool_request.file_path:
                            if tool_request.file_path not in requested_files:
                                file_content = self.read_file_content(
                                    tool_request.file_path,
                                    tool_request.start_line,
                                    tool_request.end_line
                                )
                                messages.append({
                                    "role": "user",
                                    "content": f"File content for {tool_request.file_path}:\n{file_content}\n\nNow please provide your final analysis with <analysis> and <solution> blocks."
                                })
                                requested_files.add(tool_request.file_path)
                                new_files_added = True
                                logger.info(f"Provided content for {tool_request.file_path}")
                            else:
                                logger.warning(f"File {tool_request.file_path} already requested, skipping")

                    if not new_files_added:
                        # No new files to add, force final analysis
                        messages.append({
                            "role": "user",
                            "content": "Please provide your final analysis now with <analysis> and <solution> blocks."
                        })

                    iteration += 1
                    continue

                # No tool requests - extract final analysis
                analysis = self.extract_analysis(response_text)
                if analysis:
                    analysis.reasoning_trace = reasoning_trace
                    logger.info("ReAct bug analysis completed successfully")
                    return analysis

            except Exception as e:
                logger.error(f"Error in ReAct iteration {iteration + 1}: {e}")
                iteration += 1
                continue

        logger.warning("ReAct max iterations reached, creating fallback analysis")
        return self._create_fallback_analysis("Analysis attempted but max iterations reached")

    def create_analysis_pr(self, issue: Issue, analysis: BugAnalysis) -> Optional[str]:
        """Create a pull request with the bug fix"""
        if not self.repo:
            logger.warning("No repository configured - cannot create PR")
            return None

        try:
            # Create new branch
            main_ref = self.repo.get_git_ref('heads/main')
            new_branch = f"bug-surgeon/fix-issue-{issue.number}"

            try:
                self.repo.create_git_ref(
                    ref=f'refs/heads/{new_branch}',
                    sha=main_ref.object.sha
                )
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Branch {new_branch} already exists")
                else:
                    raise

            # Create analysis file
            analysis_content = f"""# Bug Analysis Report - Issue #{issue.number}

## Root Cause
{analysis.root_cause}

## Detailed Explanation  
{analysis.explanation}

## Confidence Level
{analysis.confidence}

## Reasoning Trace
"""

            for i, trace in enumerate(analysis.reasoning_trace, 1):
                analysis_content += f"\n### Step {i}\n{trace}\n"

            # Commit analysis file
            try:
                self.repo.create_file(
                    path=f"bug-analysis-{issue.number}.md",
                    message=f"🤖 Bug analysis for issue #{issue.number}",
                    content=analysis_content,
                    branch=new_branch
                )
            except Exception as e:
                logger.warning(f"Could not create analysis file: {e}")

            # Create PR
            pr_body = f"""🤖 **Automated Bug Analysis**

**Issue**: #{issue.number} - {issue.title}

**Root Cause**: {analysis.root_cause}

**Confidence**: {analysis.confidence}

**Analysis**: {analysis.explanation}

---
*Generated by Claude Code Bug Surgeon*
*Review the analysis and apply fixes as appropriate*
"""

            pr = self.repo.create_pull_request(
                title=f"🔧 Bug Analysis: {issue.title}",
                body=pr_body,
                head=new_branch,
                base="main"
            )

            logger.info(f"Created PR #{pr.number}: {pr.html_url}")
            return pr.html_url

        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return None


def main():
    """Main entry point for GitHub Actions and local testing"""
    # Load environment variables from .env file
    load_env_file()

    logger.info("Starting Bug Surgeon...")

    try:
        surgeon = BugSurgeon()

        # Get issue context from environment or user input
        issue_number = os.getenv('ISSUE_NUMBER')
        issue_body = os.getenv('ISSUE_BODY')

        if not issue_body:
            # For local testing - prompt for input
            if not issue_number:
                print("\n🔍 Bug Surgeon - Local Mode")
                print("=" * 40)
                print("Enter bug description (or 'demo' for a test with examples/auth.py):")

                user_input = input("> ").strip()

                if user_input.lower() == 'demo':
                    issue_body = """
I'm getting this error in my Python authentication module:

```
Traceback (most recent call last):
  File "examples/auth.py", line 42, in authenticate_user
    return user.id
AttributeError: 'NoneType' object has no attribute 'id'
```

Context:
- This error happens when users try to log in
- It was working fine before our latest deployment  
- Multiple users are reporting they can't access their accounts
- The error occurs after entering valid credentials
- Our user database and sessions table seem normal

The authenticate_user function in examples/auth.py is throwing this error on line 42.
"""
                    print("🔍 Using demo bug report with examples/auth.py")
                else:
                    print("Enter full bug description (press Enter twice when done):")
                    lines = [user_input] if user_input else []
                    while True:
                        line = input()
                        if line == "" and lines:
                            break
                        lines.append(line)
                    issue_body = "\n".join(lines)

        if not issue_body and issue_number and surgeon.repo:
            # Fetch issue from GitHub
            issue = surgeon.repo.get_issue(int(issue_number))
            issue_body = f"Title: {issue.title}\n\nDescription:\n{issue.body}"

        if not issue_body:
            logger.error("No issue description provided")
            sys.exit(1)

        # Perform analysis
        analysis = surgeon.analyze_bug(issue_body)

        if not analysis:
            logger.error("Bug analysis failed")
            sys.exit(1)

        # Output results
        print("\n" + "=" * 50)
        print("BUG ANALYSIS RESULTS")
        print("=" * 50)
        print(f"🔍 Root Cause: {analysis.root_cause}")
        print(f"📊 Confidence: {analysis.confidence}")
        print(f"📝 Explanation: {analysis.explanation}")

        if analysis.reasoning_trace:
            print(f"\n🧠 Reasoning Steps:")
            for i, trace in enumerate(analysis.reasoning_trace, 1):
                print(f"   {i}. {trace[:100]}...")

        # Create PR if in GitHub Actions mode
        if surgeon.repo and issue_number:
            issue = surgeon.repo.get_issue(int(issue_number))
            pr_url = surgeon.create_analysis_pr(issue, analysis)
            if pr_url:
                print(f"\n📋 Created PR: {pr_url}")

        logger.info("Bug Surgeon completed successfully")

    except Exception as e:
        logger.error(f"Bug Surgeon failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()