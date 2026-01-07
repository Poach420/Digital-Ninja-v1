"""
AI Application Builder Service
Generates complete, functional applications from natural language prompts using OpenAI
"""

import os
import json
import logging
from typing import Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


# Cleaned up and fixed AIBuilderService class
class AIBuilderService:
    def _generate_readme(self, app_structure, tech_stack):
        """
        Generate a README.md file for the generated app.
        """
        app_name = app_structure.get('app_name', 'Generated App')
        description = app_structure.get('description', '')
        setup = app_structure.get('setup_instructions', '')
        deployment = app_structure.get('deployment_notes', '')
        tech = ', '.join(f"{k}: {v}" for k, v in (tech_stack or {}).items())
        return f"""# {app_name}\n\n{description}\n\n## Tech Stack\n{tech}\n\n## Setup\n{setup}\n\n## Deployment\n{deployment}\n"""

    def _add_deployment_configs(self, app_structure, tech_stack):
        """
        Adds deployment configuration files (vercel.json, render.yaml, .env.example) to the app structure if not already present.
        """
        files = app_structure.get('files', [])
        # Add vercel.json if not present
        if not any(f['path'] == 'vercel.json' for f in files):
            files.append({
                "path": "vercel.json",
                "content": '{\n  "version": 2,\n  "builds": [{ "src": "backend/server.py", "use": "@vercel/python" }]\n}',
                "language": "json"
            })
        # Add render.yaml if not present
        if not any(f['path'] == 'render.yaml' for f in files):
            files.append({
                "path": "render.yaml",
                "content": 'services:\n  - type: web\n    name: backend\n    env: python\n    buildCommand: "pip install -r requirements.txt"\n    startCommand: "uvicorn builder_server:app --host 0.0.0.0 --port 10000"\n',
                "language": "yaml"
            })
        # Add .env.example if not present
        if not any(f['path'] == '.env.example' for f in files):
            files.append({
                "path": ".env.example",
                "content": 'MONGODB_URI=\nJWT_SECRET=\nOPENAI_API_KEY=\nGOOGLE_CLIENT_ID=\nGOOGLE_CLIENT_SECRET=\nCORS_ORIGINS=http://localhost:3000\n',
                "language": "env"
            })

    def _get_fallback_for_prompt(self, prompt, tech_stack):
        """
        Returns a minimal fallback app structure if AI generation fails.
        """
        return {
            "app_name": "fallback-app",
            "description": f"Fallback app for prompt: {prompt}",
            "files": [
                {
                    "path": "frontend/src/App.js",
                    "content": "// Minimal React app placeholder\nexport default function App() { return <div>Fallback App</div>; }",
                    "language": "javascript"
                },
                {
                    "path": "backend/server.py",
                    "content": "# Minimal FastAPI app placeholder\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root():\n    return {'message': 'Fallback API'}",
                    "language": "python"
                },
                {
                    "path": "README.md",
                    "content": f"# Fallback Project\n\nPrompt: {prompt}\nTech stack: {tech_stack}\n\nThis is a fallback project structure.",
                    "language": "markdown"
                }
            ]
        }

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_app_structure(self, prompt: str, tech_stack: Dict[str, str]) -> Dict:
        """Generate complete application structure from prompt"""
        system_prompt = f"""You are Base44 AI - an expert full-stack developer who generates COMPLETE, PRODUCTION-READY applications instantly.

Tech Stack:
- Accessible components (ARIA labels)
- Clean, maintainable code structure
- Production-grade security practices

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no code blocks):
{{
  "app_name": "descriptive-app-name",
  "description": "Brief description of what the app does",
  "files": [
    {{
      "path": "frontend/src/App.js",
      "content": "COMPLETE WORKING REACT CODE HERE",
      "language": "javascript"
    }},
    {{
      "path": "frontend/src/App.css",
      "content": "COMPLETE CSS STYLING HERE",
      "language": "css"
    }},
    {{
      "path": "frontend/package.json",
      "content": "PACKAGE.JSON WITH DEPENDENCIES",
      "language": "json"
    }}
  ],
  "setup_instructions": "Installation and setup steps",
  "deployment_notes": "Deployment guidance"
}}

RULES:
- Return ONLY the JSON object
- NO markdown formatting
- NO code blocks (```)
- NO explanatory text before or after the JSON
- Include complete working code in each file"""

        user_prompt = f"""Generate a COMPLETE, FUNCTIONAL, WORKING application for: {prompt}

Remember:
1. Make it IMMEDIATELY runnable - no placeholders
2. Include REAL logic and functionality
3. Style it professionally with CSS
4. Add all necessary dependencies to package.json
5. Make it look good and work perfectly

Return the JSON structure with complete code now."""

        try:
            logger.info(f"Generating app for prompt: {prompt}")

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"Received response, length: {len(response_text)}")

            # Clean response if needed
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            app_structure = json.loads(response_text)

            # Validate structure
            if not app_structure.get('files'):
                raise ValueError("No files generated in response")

            # Ensure package.json exists
            has_package_json = any(f['path'].endswith('package.json') for f in app_structure['files'])
            if not has_package_json:
                app_structure['files'].append({
                    "path": "frontend/package.json",
                    "content": self._generate_package_json(app_structure.get('app_name', 'generated-app')),
                    "language": "json"
                })

            # Add deployment configs if not present
            self._add_deployment_configs(app_structure, tech_stack)

            # Add README if not present
            if not any(f['path'].endswith('README.md') for f in app_structure['files']):
                app_structure['files'].append({
                    "path": "README.md",
                    "content": self._generate_readme(app_structure, tech_stack),
                    "language": "markdown"
                })

            logger.info(f"Successfully generated app with {len(app_structure['files'])} files")
            return app_structure

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._get_fallback_for_prompt(prompt, tech_stack)
        except Exception as e:
            import traceback
            logger.error(f"AI generation error: {e}")
            logger.error(traceback.format_exc())
            try:
                # If OpenAI API returned a response, log it
                if 'response' in locals():
                    logger.error(f"OpenAI response: {getattr(response, 'choices', None)}")
            except Exception as log_e:
                logger.error(f"Error logging OpenAI response: {log_e}")
            return self._get_fallback_for_prompt(prompt, tech_stack)
    
    def _generate_package_json(self, app_name: str) -> str:
        """Generate a standard package.json"""
        package = {
            "name": app_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        return json.dumps(package, indent=2)
    
ai_builder = AIBuilderService()