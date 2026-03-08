"""
Script execution service for AI-generated transformations
"""

import json
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import traceback

from app.core.config import settings
from app.services.ai import get_ai_service
from loguru import logger


class ScriptExecutionService:
    """Service for generating, testing, and executing AI-generated scripts."""
    
    def __init__(self):
        self.storage_path = Path(settings.DATA_STORAGE_PATH)
        self.scripts_path = self.storage_path / "scripts"
        self.scripts_path.mkdir(parents=True, exist_ok=True)
        self.sandbox_path = self.storage_path / "sandbox"
        self.sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Allowed modules for sandbox execution
        self.allowed_modules = {
            'json', 'csv', 'os', 'sys', 'pathlib', 're', 'collections',
            'datetime', 'typing', 'copy', 'math', 'statistics',
            'PIL', 'cv2', 'numpy', 'pandas',
        }
        
        # Blocked dangerous operations
        self.blocked_patterns = [
            'import os.system', 'subprocess', 'eval(', 'exec(',
            'compile(', 'open(', 'file(', '__import__',
            'socket', 'urllib', 'requests', 'http',
            'shutil.rmtree', 'os.remove', 'os.unlink',
        ]
    
    def _get_ai_service(self, api_key: Optional[str], base_url: Optional[str], model: Optional[str]):
        """Get AI service instance."""
        return get_ai_service(api_key=api_key, base_url=base_url, model=model)
    
    async def generate_script(
        self,
        source_format: str,
        target_format: str,
        sample_data: Optional[Dict[str, Any]] = None,
        requirements: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate transformation script using AI.
        
        Args:
            source_format: Description of source format
            target_format: Description of target format
            sample_data: Sample input data
            requirements: Additional requirements/instructions
            api_key: Custom API key
            base_url: Custom API URL
            model: Custom model name
        
        Returns:
            Generated script and metadata
        """
        service = self._get_ai_service(api_key, base_url, model)
        
        # Build prompt
        system_prompt = """You are an expert Python developer specializing in data transformation.
Generate clean, efficient Python code for converting data between formats.

Requirements:
1. Output ONLY valid Python code, no explanations
2. Include proper error handling with try-except
3. Use type hints
4. Include docstrings
5. The script must define these functions:
   - `transform(input_data)` - main transformation function
   - `validate(input_data)` - optional validation function (return True/False)
6. Input data will be passed as Python dict/list
7. Return transformed data as Python dict/list
8. Do NOT use file I/O - data is passed in memory
9. Do NOT use network operations
10. Keep it simple and focused on the transformation

The script will be executed in a sandboxed environment."""

        user_message = f"""Generate a Python script to transform data:

**Source format:** {source_format}

**Target format:** {target_format}

{f"**Sample input:**\\n```json\\n{json.dumps(sample_data, indent=2, ensure_ascii=False)}\\n```" if sample_data else ""}

{f"**Additional requirements:**\\n{requirements}" if requirements else ""}

Generate the complete Python script with `transform()` and `validate()` functions."""

        try:
            script_code = await service._call_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            
            # Clean up code (remove markdown code blocks if present)
            if script_code.startswith("```python"):
                script_code = script_code.split("```python", 1)[1]
                script_code = script_code.rsplit("```", 1)[0]
            elif script_code.startswith("```"):
                script_code = script_code.split("```", 1)[1]
                script_code = script_code.rsplit("```", 1)[0]
            
            script_code = script_code.strip()
            
            return {
                "success": True,
                "script": script_code,
                "source_format": source_format,
                "target_format": target_format,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def validate_script_security(self, script_code: str) -> Dict[str, Any]:
        """
        Validate script for security issues.
        
        Returns:
            Validation result with issues found
        """
        issues = []
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in script_code:
                issues.append(f"Blocked pattern found: {pattern}")
        
        # Check imports
        import_lines = [line.strip() for line in script_code.split('\n') 
                       if line.strip().startswith('import ') or line.strip().startswith('from ')]
        
        for line in import_lines:
            module = line.split()[1].split('.')[0] if 'from ' in line else line.split()[1].split('.')[0]
            if module not in self.allowed_modules and module not in ['__future__']:
                issues.append(f"Module not allowed: {module}")
        
        # Check for dangerous operations
        dangerous_funcs = ['exec', 'eval', 'compile', '__import__', 'open', 'input']
        for func in dangerous_funcs:
            if f'{func}(' in script_code and not f'#{func}' in script_code:
                # Check if it's actually being called (not in string or comment)
                for line in script_code.split('\n'):
                    if f'{func}(' in line and not line.strip().startswith('#') and f'"{func}' not in line and f"'{func}" not in line:
                        issues.append(f"Dangerous function call: {func}()")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": [] if len(issues) == 0 else ["Script may contain unsafe operations"],
        }
    
    async def test_script(
        self,
        script_code: str,
        test_data: Any,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Test script with sample data in sandbox.
        
        Args:
            script_code: Python script to test
            test_data: Test input data
            timeout: Execution timeout in seconds
        
        Returns:
            Test result with output and any errors
        """
        # First validate security
        security_check = self.validate_script_security(script_code)
        if not security_check["valid"]:
            return {
                "success": False,
                "error": "Script failed security check",
                "security_issues": security_check["issues"],
            }
        
        # Create temporary script file
        script_file = self.sandbox_path / f"test_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        result_file = self.sandbox_path / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Wrap script for testing
            wrapped_code = f'''
import json
import sys

{script_code}

if __name__ == "__main__":
    try:
        # Load input data
        input_data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {{}}
        
        # Validate if function exists
        if 'validate' in dir():
            if not validate(input_data):
                print(json.dumps({{"success": False, "error": "Validation failed"}}))
                sys.exit(0)
        
        # Transform
        result = transform(input_data)
        
        print(json.dumps({{"success": True, "output": result}}, default=str))
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))
'''
            
            script_file.write_text(wrapped_code)
            
            # Execute in subprocess
            proc = await asyncio.create_subprocess_exec(
                'python3', str(script_file), json.dumps(test_data),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.sandbox_path),
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "error": f"Script execution timed out ({timeout}s)",
                }
            
            # Parse output
            output = stdout.decode('utf-8', errors='replace')
            errors = stderr.decode('utf-8', errors='replace')
            
            try:
                result = json.loads(output.strip().split('\n')[-1])
                result["stderr"] = errors if errors else None
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Invalid output: {output}",
                    "stderr": errors,
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        finally:
            # Cleanup
            if script_file.exists():
                script_file.unlink()
            if result_file.exists():
                result_file.unlink()
    
    async def execute_script(
        self,
        script_code: str,
        input_data: Any,
        script_name: Optional[str] = None,
        timeout: int = 300,
        save_script: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute script on actual data.
        
        Args:
            script_code: Python script to execute
            input_data: Input data to transform
            script_name: Optional name for saved script
            timeout: Execution timeout in seconds
            save_script: Whether to save script for future use
        
        Returns:
            Execution result
        """
        # Security check
        security_check = self.validate_script_security(script_code)
        if not security_check["valid"]:
            return {
                "success": False,
                "error": "Script failed security check",
                "security_issues": security_check["issues"],
            }
        
        # Save script
        if save_script:
            script_name = script_name or f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            script_file = self.scripts_path / script_name
            script_file.write_text(script_code)
        
        # Execute
        result = await self.test_script(script_code, input_data, timeout)
        
        if save_script and result.get("success"):
            result["script_name"] = script_name
            result["script_path"] = str(script_file)
        
        return result
    
    def list_saved_scripts(self) -> List[Dict[str, Any]]:
        """List all saved scripts."""
        scripts = []
        
        for script_file in self.scripts_path.glob("*.py"):
            stat = script_file.stat()
            scripts.append({
                "name": script_file.name,
                "path": str(script_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        return sorted(scripts, key=lambda x: x["created"], reverse=True)
    
    def get_script(self, script_name: str) -> Optional[str]:
        """Get saved script content."""
        script_file = self.scripts_path / script_name
        if script_file.exists():
            return script_file.read_text()
        return None
    
    def delete_script(self, script_name: str) -> bool:
        """Delete a saved script."""
        script_file = self.scripts_path / script_name
        if script_file.exists():
            script_file.unlink()
            return True
        return False


# Singleton
script_service = ScriptExecutionService()