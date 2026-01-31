"""
AI Provider - Handles AI integration with multiple providers (DeepSeek, OpenAI, etc.)
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .exceptions import AIProviderError, APIKeyMissingError


@dataclass
class AIResponse:
    """Response from AI provider"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    confidence: Optional[float] = None


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """Send chat completion request"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the API connection works"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider"""
        pass


class DeepSeekProvider(AIProvider):
    """DeepSeek AI provider - very cost effective"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        # DeepSeek uses OpenAI-compatible API
        try:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com",
            )
        except Exception as e:
            raise AIProviderError(f"Failed to initialize DeepSeek client: {e}")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """Send chat completion request to DeepSeek"""
        try:
            # Merge default parameters with kwargs
            params = {
                'model': self.model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.7),
                'max_tokens': kwargs.get('max_tokens', 2000),
                **self.kwargs
            }
            
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            # DeepSeek is very cheap: ~$0.14 per 1M input tokens, $0.28 per 1M output tokens
            cost_estimate = None
            if tokens_used:
                # Rough cost estimate (assuming 50/50 input/output split)
                cost_estimate = (tokens_used / 1_000_000) * 0.21  # Average rate
            
            return AIResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            raise AIProviderError(f"DeepSeek API error: {e}")
    
    def test_connection(self) -> bool:
        """Test DeepSeek API connection"""
        try:
            messages = [{"role": "user", "content": "Hi"}]
            response = self.chat_completion(messages, max_tokens=10)
            return bool(response.content)
        except:
            return False
    
    @property
    def provider_name(self) -> str:
        return "deepseek"


class OpenAIProvider(AIProvider):
    """OpenAI provider (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise AIProviderError("OpenAI package not installed. Run: pip install openai")
        
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            raise AIProviderError(f"Failed to initialize OpenAI client: {e}")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """Send chat completion request to OpenAI"""
        try:
            params = {
                'model': self.model,
                'messages': messages,
                'temperature': kwargs.get('temperature', 0.7),
                'max_tokens': kwargs.get('max_tokens', 2000),
                **self.kwargs
            }
            
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            # OpenAI pricing (approximate)
            cost_estimate = None
            if tokens_used and self.model:
                if "gpt-4" in self.model:
                    cost_estimate = (tokens_used / 1000) * 0.03  # $30 per 1M tokens
                elif "gpt-3.5" in self.model:
                    cost_estimate = (tokens_used / 1000) * 0.002  # $2 per 1M tokens
            
            return AIResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            raise AIProviderError(f"OpenAI API error: {e}")
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            messages = [{"role": "user", "content": "Hi"}]
            response = self.chat_completion(messages, max_tokens=10)
            return bool(response.content)
        except:
            return False
    
    @property
    def provider_name(self) -> str:
        return "openai"


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    @staticmethod
    def create_provider(
        provider_name: str, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AIProvider:
        """Create an AI provider instance"""
        
        # Get API key from environment if not provided
        if not api_key:
            if provider_name == "deepseek":
                api_key = os.getenv("DEEPSEEK_API_KEY")
            elif provider_name == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            else:
                raise AIProviderError(f"Unknown provider: {provider_name}")
        
        if not api_key:
            raise APIKeyMissingError(f"API key not found for {provider_name}")
        
        # Set default models if not specified
        if not model:
            if provider_name == "deepseek":
                model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            elif provider_name == "openai":
                model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Create provider instance
        if provider_name == "deepseek":
            return DeepSeekProvider(api_key, model, **kwargs)
        elif provider_name == "openai":
            return OpenAIProvider(api_key, model, **kwargs)
        else:
            raise AIProviderError(f"Unsupported provider: {provider_name}")


class AIService:
    """High-level AI service that handles GitSmart-specific prompting"""
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        
    def ask_about_repository(
        self, 
        question: str, 
        repo_context: Dict[str, Any],
        output_format: str = "plain"
    ) -> AIResponse:
        """Ask a question about the repository with context"""
        
        system_prompt = self._get_system_prompt(output_format)
        user_prompt = self._format_repository_query(question, repo_context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.provider.chat_completion(messages, temperature=0.7)
    
    def explain_file(
        self, 
        filepath: str, 
        file_context: Dict[str, Any],
        output_format: str = "plain"
    ) -> AIResponse:
        """Explain a file based on its git history and context"""
        
        system_prompt = self._get_system_prompt(output_format, task="explain")
        user_prompt = self._format_file_explanation_query(filepath, file_context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.provider.chat_completion(messages, temperature=0.6)
    
    def understand_decision(
        self,
        decision: str,
        context: Dict[str, Any]
    ) -> AIResponse:
        """Process and enhance a decision with context"""
        
        system_prompt = """You are a decision documentation assistant. Your job is to help capture and contextualize decisions made during software development.

Given a decision and its git context, provide:
1. A clear summary of what was decided
2. The apparent reasoning (based on git context)
3. Any relevant technical details
4. Potential future considerations

Be concise but comprehensive."""

        user_prompt = f"""
Decision: {decision}

Context:
- Branch: {context.get('branch', 'unknown')}
- Recent commits: {[c.get('message', '') for c in context.get('recent_commits', [])[:5]]}
- Modified files: {context.get('modified_files', [])}
- Current date: {context.get('timestamp', 'unknown')}

Please provide a structured analysis of this decision.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.provider.chat_completion(messages, temperature=0.5)
    
    def _get_system_prompt(self, output_format: str = "plain", task: str = "ask") -> str:
        """Get system prompt based on output format and task"""
        
        base_prompt = """You are GitSmart, an AI assistant that helps developers understand git repositories. You analyze git history, commit messages, file evolution, and code context to provide helpful insights.

Your responses should be:
- Accurate and based on the provided git context
- Helpful for understanding why code exists and how it evolved
- Clear and well-structured
- Specific, citing commit hashes and dates when available

Never make up commit hashes, dates, or information not present in the context."""

        if output_format == "business":
            base_prompt += """

Format your responses for business stakeholders (product managers, designers, executives):
- Lead with business impact and implications
- Explain technical concepts in accessible language
- Include timeline and key people information
- Focus on outcomes and decisions rather than implementation details"""

        elif output_format == "json":
            base_prompt += """

Return your response as valid JSON with these fields:
- "summary": Main answer to the question
- "details": Additional technical details
- "sources": Array of relevant commits/files
- "confidence": Your confidence level (0-1)"""

        if task == "explain":
            base_prompt += """

You are specifically explaining file evolution and purpose. Include:
- Why the file was created
- How it has evolved over time
- Key changes and the reasoning behind them
- Current role and relationships to other files"""

        return base_prompt
    
    def _format_repository_query(self, question: str, context: Dict[str, Any]) -> str:
        """Format a repository question with context"""
        
        # Extract key context elements
        repo_stats = context.get('repo_stats', {})
        recent_commits = context.get('recent_commits', [])
        relevant_commits = context.get('relevant_commits', [])
        
        prompt = f"""Question: {question}

Repository Overview:
- {repo_stats.get('commit_count', 0)} commits by {repo_stats.get('contributor_count', 0)} contributors
- Primary language: {repo_stats.get('primary_language', 'Unknown')}
- Age: {repo_stats.get('age_days', 0)} days
- Current branch: {repo_stats.get('current_branch', 'unknown')}
"""

        if recent_commits:
            prompt += "\nRecent Commits:\n"
            for commit in recent_commits[:10]:
                prompt += f"- {commit.get('short_hash', '')}: {commit.get('message', '')[:80]}\n"
        
        if relevant_commits:
            prompt += "\nRelevant Commits:\n"
            for commit in relevant_commits[:15]:
                prompt += f"- {commit.get('short_hash', '')}: {commit.get('message', '')}\n"
                if commit.get('files_changed'):
                    prompt += f"  Files: {', '.join(commit['files_changed'][:5])}\n"
        
        prompt += "\nPlease answer the question based on this git repository context."
        
        return prompt
    
    def _format_file_explanation_query(self, filepath: str, context: Dict[str, Any]) -> str:
        """Format a file explanation query with context"""
        
        file_history = context.get('file_history', {})
        related_files = context.get('related_files', [])
        
        prompt = f"""Please explain the file: {filepath}

File Information:
- Exists: {file_history.get('exists', False)}
- Created: {file_history.get('creation_date', 'Unknown')}
- Last modified: {file_history.get('last_modified', 'Unknown')}
- Total commits: {file_history.get('total_commits', 0)}
- Authors: {', '.join(file_history.get('authors', [])[:5])}
- Lines of code: {file_history.get('lines_of_code', 'Unknown')}
"""

        recent_changes = file_history.get('recent_changes', [])
        if recent_changes:
            prompt += "\nRecent Changes:\n"
            for commit in recent_changes:
                prompt += f"- {commit.get('short_hash', '')}: {commit.get('message', '')}\n"
                prompt += f"  Date: {commit.get('date', '')}, Author: {commit.get('author', '')}\n"
        
        if related_files:
            prompt += f"\nRelated Files:\n"
            for related_file, relationship in related_files:
                prompt += f"- {related_file} ({relationship})\n"
        
        prompt += "\nProvide a comprehensive explanation of this file's purpose, evolution, and current role."
        
        return prompt