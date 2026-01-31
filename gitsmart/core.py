"""
GitSmart Core - Main orchestrator that ties together git analysis and AI
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .git_context import GitContextExtractor, RepoStats, FileHistory
from .ai_provider import AIProviderFactory, AIService, AIResponse
from .storage import KnowledgeStorage, GitNotesStorage
from .config import Config
from .exceptions import GitSmartError, NotAGitRepoError


class GitSmart:
    """Main GitSmart class that orchestrates git analysis and AI insights"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        
        # Initialize components
        try:
            self.git_extractor = GitContextExtractor(str(self.repo_path))
        except NotAGitRepoError as e:
            raise e
        
        self.config = Config(self.repo_path)
        self.storage = GitNotesStorage(self.repo_path)
        
        # Initialize AI service (lazy loaded)
        self._ai_service: Optional[AIService] = None
    
    def _get_ai_service(self) -> AIService:
        """Lazy load AI service based on configuration"""
        if self._ai_service is None:
            ai_config = self.config.get_ai_config()
            
            provider = AIProviderFactory.create_provider(
                provider_name=ai_config['provider'],
                api_key=ai_config.get('api_key'),
                model=ai_config.get('model')
            )
            
            self._ai_service = AIService(provider)
        
        return self._ai_service
    
    def ask(
        self, 
        question: str, 
        max_commits: int = 100,
        output_format: str = "plain",
        include_impact: bool = False
    ) -> str:
        """Ask a question about the repository"""
        
        # Gather repository context
        context = self._build_repository_context(question, max_commits)
        
        # Include stored knowledge/decisions
        relevant_memories = self.storage.search_memories(question)
        if relevant_memories:
            context['stored_knowledge'] = relevant_memories
        
        # Get AI response
        ai_service = self._get_ai_service()
        response = ai_service.ask_about_repository(
            question, 
            context, 
            output_format=output_format
        )
        
        # Store the query and response for learning (convert context to JSON-serializable format)
        import json
        try:
            # Test if context is JSON-serializable
            json.dumps(context)
            serializable_context = context
        except TypeError:
            # If not, convert datetime objects to strings
            serializable_context = self._make_context_serializable(context)
        
        self.storage.store_query(question, response.content, serializable_context)
        
        # Format response based on output_format
        if output_format == "json":
            return response.content
        elif include_impact:
            return self._add_business_context(response.content, context)
        else:
            return response.content
    
    def explain(
        self, 
        filepath: str,
        include_history: bool = False,
        include_usage: bool = False,
        include_impact: bool = False
    ) -> str:
        """Explain a file or directory"""
        
        # Handle directory vs file
        path = Path(self.repo_path) / filepath
        if path.is_dir():
            return self._explain_directory(filepath, include_impact)
        else:
            return self._explain_file(filepath, include_history, include_usage, include_impact)
    
    def remember(
        self, 
        decision: str, 
        memory_type: str = "decision",
        tags: Optional[List[str]] = None
    ) -> str:
        """Store a decision or note with current git context"""
        
        # Capture current context
        current_context = self.git_extractor.get_current_context()
        
        # Enhance with AI understanding if possible
        try:
            ai_service = self._get_ai_service()
            ai_response = ai_service.understand_decision(decision, current_context)
            enhanced_content = ai_response.content
        except Exception:
            # If AI fails, just store the raw decision
            enhanced_content = decision
        
        # Store the memory
        memory_id = self.storage.store_memory(
            content=decision,
            enhanced_content=enhanced_content,
            context=current_context,
            memory_type=memory_type,
            tags=tags or []
        )
        
        return memory_id
    
    def get_repo_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        stats = self.git_extractor.get_repo_stats()
        return stats.to_dict()
    
    def get_status(self) -> Dict[str, Any]:
        """Get GitSmart status information"""
        repo_stats = self.git_extractor.get_repo_stats()
        config_info = self.config.get_all()
        knowledge_info = self.storage.get_statistics()
        
        return {
            'repo': {
                'commit_count': repo_stats.commit_count,
                'file_count': repo_stats.file_count,
                'current_branch': repo_stats.current_branch,
                'age_days': repo_stats.age_days,
                'primary_language': repo_stats.primary_language
            },
            'config': {
                'ai_provider': config_info.get('ai', {}).get('provider', 'not configured'),
                'ai_model': config_info.get('ai', {}).get('model', 'not configured'),
                'api_key_configured': bool(config_info.get('ai', {}).get('api_key'))
            },
            'knowledge': knowledge_info
        }
    
    def test_ai_connection(self) -> bool:
        """Test AI provider connection"""
        try:
            ai_service = self._get_ai_service()
            return ai_service.provider.test_connection()
        except Exception:
            return False
    
    def _build_repository_context(self, question: str, max_commits: int) -> Dict[str, Any]:
        """Build context for repository questions"""
        
        # Get overall repository stats
        repo_stats = self.git_extractor.get_repo_stats()
        
        # Get recent commits
        recent_commits = self.git_extractor.get_recent_commits(count=20)
        
        # Search for relevant commits based on the question
        relevant_commits = self.git_extractor.search_commits(question, max_results=max_commits)
        
        # Get current context
        current_context = self.git_extractor.get_current_context()
        
        return {
            'repo_stats': repo_stats.to_dict(),
            'recent_commits': [c.to_dict() for c in recent_commits],
            'relevant_commits': [c.to_dict() for c in relevant_commits],
            'current_context': current_context,
            'question': question
        }
    
    def _explain_file(
        self, 
        filepath: str, 
        include_history: bool,
        include_usage: bool,
        include_impact: bool
    ) -> str:
        """Explain a specific file"""
        
        # Get file history
        file_history = self.git_extractor.get_file_history(filepath)
        
        # Get related files if requested
        related_files = []
        if include_usage:
            related_files = self.git_extractor.find_related_files(filepath)
        
        # Build context
        context = {
            'file_history': file_history.to_dict(),
            'related_files': related_files,
            'filepath': filepath
        }
        
        # Get AI explanation
        ai_service = self._get_ai_service()
        response = ai_service.explain_file(filepath, context)
        
        # Store for future reference
        self.storage.store_explanation(filepath, response.content, context)
        
        if include_impact:
            return self._add_business_context(response.content, context)
        else:
            return response.content
    
    def _explain_directory(self, dirpath: str, include_impact: bool) -> str:
        """Explain a directory by analyzing its contents"""
        
        full_path = self.repo_path / dirpath
        
        # Get directory contents
        try:
            files = [f for f in full_path.iterdir() if f.is_file()]
            subdirs = [d for d in full_path.iterdir() if d.is_dir()]
        except OSError:
            return f"Cannot access directory: {dirpath}"
        
        # Analyze file types and patterns
        file_analysis = self._analyze_directory_contents(files, subdirs)
        
        # Get relevant commits for this directory
        relevant_commits = self.git_extractor.search_commits(dirpath, max_results=20)
        
        context = {
            'directory': dirpath,
            'file_analysis': file_analysis,
            'relevant_commits': [c.to_dict() for c in relevant_commits]
        }
        
        # Simple directory explanation (could be enhanced with AI)
        explanation = f"## Directory: {dirpath}\n\n"
        explanation += f"Contains {len(files)} files and {len(subdirs)} subdirectories.\n\n"
        
        if file_analysis['languages']:
            explanation += "**File Types:**\n"
            for lang, count in file_analysis['languages'].items():
                explanation += f"- {lang}: {count} files\n"
            explanation += "\n"
        
        if relevant_commits:
            explanation += "**Recent Activity:**\n"
            for commit in relevant_commits[:5]:
                explanation += f"- {commit.short_hash}: {commit.message[:80]}\n"
        
        return explanation
    
    def _analyze_directory_contents(self, files: List[Path], subdirs: List[Path]) -> Dict[str, Any]:
        """Analyze the contents of a directory"""
        
        # File type analysis
        extensions = {}
        languages = {}
        
        for file in files:
            ext = file.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
            
            # Map extensions to languages (simplified)
            lang_map = {
                '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.go': 'Go',
                '.rs': 'Rust', '.php': 'PHP', '.rb': 'Ruby'
            }
            
            if ext in lang_map:
                lang = lang_map[ext]
                languages[lang] = languages.get(lang, 0) + 1
        
        return {
            'file_count': len(files),
            'directory_count': len(subdirs),
            'extensions': extensions,
            'languages': languages,
            'subdirectories': [d.name for d in subdirs]
        }
    
    def _add_business_context(self, technical_response: str, context: Dict[str, Any]) -> str:
        """Add business context to a technical response"""
        
        # This is a simplified version - could be much more sophisticated
        business_context = "\n\n## Business Impact\n"
        
        # Look for business indicators in the context
        repo_stats = context.get('repo_stats', {})
        
        if repo_stats.get('primary_language'):
            business_context += f"- **Technology Stack**: {repo_stats['primary_language']}-based application\n"
        
        if repo_stats.get('contributor_count', 0) > 1:
            business_context += f"- **Team Size**: {repo_stats['contributor_count']} contributors\n"
        
        if repo_stats.get('age_days', 0) > 30:
            age_months = repo_stats['age_days'] // 30
            business_context += f"- **Project Maturity**: {age_months} months old\n"
        
        # Add context about recent activity
        recent_commits = context.get('recent_commits', [])
        if recent_commits:
            recent_authors = set(c.get('author', '') for c in recent_commits[:10])
            business_context += f"- **Recent Activity**: {len(recent_commits)} commits by {len(recent_authors)} developers\n"
        
        return technical_response + business_context
    
    def _make_context_serializable(self, obj):
        """Convert a context object to be JSON-serializable"""
        import json
        from datetime import datetime
        
        def convert_obj(item):
            if isinstance(item, datetime):
                return item.isoformat()
            elif isinstance(item, dict):
                return {k: convert_obj(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [convert_obj(i) for i in item]
            else:
                return item
        
        return convert_obj(obj)