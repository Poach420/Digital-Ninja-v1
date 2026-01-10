"""
Discussion Mode Service
Plan and brainstorm without consuming credits or making changes
Inspired by Base44's discussion mode
"""
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from datetime import datetime, timezone
import os

logger = logging.getLogger(__name__)


class DiscussionService:
    """Handle planning discussions without affecting project"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def discuss(
        self,
        message: str,
        project_context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Have a planning discussion without making changes
        
        Args:
            message: User's message/question
            project_context: Current project state (read-only)
            conversation_history: Previous messages in discussion
            
        Returns:
            AI response with suggestions and plans
        """
        try:
            # Build system message
            system_message = """You are an AI assistant helping users plan and design their applications.

IMPORTANT RULES:
1. This is DISCUSSION MODE - you're helping plan, NOT building or making changes
2. Provide suggestions, ideas, and recommendations
3. Ask clarifying questions to understand requirements better
4. Discuss trade-offs and best practices
5. Help break down complex features into steps
6. DO NOT generate code or make file changes
7. Focus on planning, architecture, and design decisions

When user asks about features, discuss:
- How it would work
- What technologies to use
- Potential challenges
- Alternative approaches
- Next steps to implement

Be conversational, helpful, and collaborative."""

            # Build context about current project
            context_info = ""
            if project_context:
                file_count = len(project_context.get("files", []))
                project_name = project_context.get("name", "your project")
                context_info = f"\n\nCurrent Project: {project_name} ({file_count} files)"
            
            # Build conversation
            messages = [
                {"role": "system", "content": system_message + context_info}
            ]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Get AI response
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.8,  # More creative for planning
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "success": True,
                "response": ai_response,
                "mode": "discussion",
                "changes_made": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Discussion error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_implementation_plan(
        self,
        feature_description: str,
        project_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a detailed implementation plan for a feature
        
        Returns step-by-step plan without implementing
        """
        try:
            prompt = f"""Create a detailed implementation plan for this feature:

Feature: {feature_description}

Generate a step-by-step plan that includes:
1. High-level overview
2. Required components/files
3. Technologies and libraries needed
4. Implementation steps in order
5. Testing strategy
6. Potential challenges and solutions
7. Estimated effort

Format as a structured plan that a developer can follow."""

            if project_context:
                prompt += f"\n\nCurrent project has {len(project_context.get('files', []))} files."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert software architect creating implementation plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            plan = response.choices[0].message.content
            
            return {
                "success": True,
                "plan": plan,
                "feature": feature_description,
                "mode": "planning",
                "ready_to_implement": True
            }
            
        except Exception as e:
            logger.error(f"Plan generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_requirements(
        self,
        requirements: str,
        ask_questions: bool = True
    ) -> Dict:
        """
        Analyze requirements and suggest clarifications
        
        Args:
            requirements: User's feature/app requirements
            ask_questions: Whether to generate clarifying questions
            
        Returns:
            Analysis with suggestions and questions
        """
        try:
            prompt = f"""Analyze these requirements:

{requirements}

Provide:
1. Summary of what's being requested
2. Key features identified
3. Technical approach suggestions
4. Potential ambiguities or missing details
"""
            
            if ask_questions:
                prompt += "5. 5-10 clarifying questions to ask the user\n"
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a requirements analyst helping clarify project needs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "analysis": analysis,
                "requirements": requirements,
                "mode": "analysis"
            }
            
        except Exception as e:
            logger.error(f"Requirements analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def suggest_improvements(
        self,
        project_context: Dict
    ) -> Dict:
        """
        Suggest improvements for existing project
        
        Args:
            project_context: Current project files and structure
            
        Returns:
            Improvement suggestions without making changes
        """
        try:
            files = project_context.get("files", [])
            file_list = "\n".join([f"- {f['path']}" for f in files[:20]])
            
            prompt = f"""Review this project and suggest improvements:

Project: {project_context.get('name', 'Application')}
Files ({len(files)} total):
{file_list}

Provide suggestions for:
1. Code organization and structure
2. Missing features or functionality
3. Performance optimizations
4. UI/UX improvements
5. Security considerations
6. Best practices to implement
7. Testing coverage
8. Documentation needs

Be specific and actionable."""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior software architect reviewing code for improvements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            suggestions = response.choices[0].message.content
            
            return {
                "success": True,
                "suggestions": suggestions,
                "project_name": project_context.get('name'),
                "mode": "review"
            }
            
        except Exception as e:
            logger.error(f"Improvement suggestion error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_approaches(
        self,
        problem: str,
        approaches: List[str]
    ) -> Dict:
        """
        Compare different implementation approaches
        
        Args:
            problem: Problem to solve
            approaches: List of approaches to compare
            
        Returns:
            Comparison with pros/cons for each
        """
        try:
            approaches_text = "\n".join([f"{i+1}. {a}" for i, a in enumerate(approaches)])
            
            prompt = f"""Compare these approaches for solving this problem:

Problem: {problem}

Approaches:
{approaches_text}

For each approach, provide:
- Pros
- Cons
- Best use cases
- Complexity level
- Recommended scenarios

Then provide your recommendation."""

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a technical advisor comparing implementation approaches."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            comparison = response.choices[0].message.content
            
            return {
                "success": True,
                "comparison": comparison,
                "problem": problem,
                "approaches_count": len(approaches),
                "mode": "comparison"
            }
            
        except Exception as e:
            logger.error(f"Approach comparison error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
