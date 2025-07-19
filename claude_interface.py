"""
Claude CLI interface module - Handles all interactions with Claude
"""
import subprocess
import json
import re
import logging
from typing import Dict, Any, Optional, Callable
from json import JSONDecodeError


class ClaudeInterface:
    def __init__(self, claude_command: str = "claude"):
        self.claude_command = claude_command
        self.logger = logging.getLogger(__name__)
        
    def execute_raw(self, prompt: str, timeout: int = 300) -> str:
        """Execute Claude with a prompt and return raw output"""
        try:
            self.logger.info("Executing Claude with prompt...")
            
            # Run Claude via subprocess
            result = subprocess.run(
                [self.claude_command],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Claude command failed: {result.stderr}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            self.logger.info("Claude execution completed successfully")
            return result.stdout
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude execution timed out after {timeout} seconds")
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute Claude: {str(e)}")
            raise
            
    def extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """Extract JSON from Claude's output"""
        # First try to find JSON between ```json and ``` markers
        json_match = re.search(r'```json\n(.*?)\n```', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON from code block: {e}")
                
        # Try to find any JSON object in the output
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_matches = re.findall(json_pattern, output)
        
        for match in json_matches:
            try:
                return json.loads(match)
            except JSONDecodeError:
                continue
                
        # Last resort: try to parse the entire output as JSON
        try:
            return json.loads(output.strip())
        except JSONDecodeError:
            self.logger.error(f"Could not extract JSON from output: {output[:200]}...")
            raise ValueError("No valid JSON found in Claude's output")
            
    def execute_json(self, prompt: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute Claude and parse JSON response"""
        output = self.execute_raw(prompt, timeout)
        return self.extract_json_from_output(output)
        
    def make_prompt_more_explicit(self, prompt: str, error: Exception) -> str:
        """Make the prompt more explicit based on error"""
        error_context = f"\n\nPREVIOUS ERROR: {str(error)}\n"
        reminder = "\nIMPORTANT: Return ONLY valid JSON, no other text. "
        
        if isinstance(error, JSONDecodeError):
            reminder += "Ensure your response is properly formatted JSON with correct syntax."
        elif isinstance(error, ValueError) and "schema" in str(error).lower():
            reminder += "Ensure all required fields are present in the JSON response."
            
        return prompt + error_context + reminder
        
    def execute_with_retry(
        self,
        phase_name: str,
        prompt: str,
        validator: Optional[Callable[[Dict[str, Any]], None]] = None,
        max_retries: int = 3,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute Claude with retry logic and validation"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries} for phase: {phase_name}")
                
                # Execute Claude
                result = self.execute_json(prompt, timeout)
                
                # Validate if validator provided
                if validator:
                    validator(result)
                    
                self.logger.info(f"Phase {phase_name} completed successfully")
                return result
                
            except (JSONDecodeError, ValueError) as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Make prompt more explicit for retry
                    prompt = self.make_prompt_more_explicit(prompt, e)
                    continue
                    
        # All retries failed
        self.logger.error(f"All retries failed for phase {phase_name}")
        raise last_error or RuntimeError(f"Failed to complete phase {phase_name}")
        
    def test_connection(self) -> bool:
        """Test if Claude CLI is available and working"""
        try:
            result = subprocess.run(
                [self.claude_command, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False