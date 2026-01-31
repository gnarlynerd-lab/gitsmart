"""
Git Context Extraction - Analyzes git repositories to extract knowledge
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

import git
from git import Repo, InvalidGitRepositoryError

from .exceptions import NotAGitRepoError, GitSmartError


@dataclass
class CommitInfo:
    """Information about a git commit"""
    hash: str
    short_hash: str
    message: str
    author: str
    email: str
    date: datetime
    files_changed: List[str]
    insertions: int
    deletions: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert datetime to ISO string for JSON serialization
        if 'date' in data and data['date']:
            data['date'] = data['date'].isoformat()
        return data


@dataclass
class FileHistory:
    """History and context for a specific file"""
    filepath: str
    exists: bool
    creation_date: Optional[datetime]
    last_modified: Optional[datetime]
    total_commits: int
    authors: List[str]
    recent_changes: List[CommitInfo]
    lines_of_code: Optional[int]
    file_size: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert CommitInfo objects to dicts
        data['recent_changes'] = [commit.to_dict() for commit in self.recent_changes]
        # Convert datetime objects to ISO strings
        for field in ['creation_date', 'last_modified']:
            if field in data and data[field]:
                data[field] = data[field].isoformat()
        return data


@dataclass
class RepoStats:
    """Overall repository statistics"""
    commit_count: int
    file_count: int
    contributor_count: int
    age_days: int
    primary_language: Optional[str]
    languages: Dict[str, int]  # language -> file count
    recent_activity: List[CommitInfo]
    branch_count: int
    current_branch: str
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['recent_activity'] = [commit.to_dict() for commit in self.recent_activity]
        return data


class GitContextExtractor:
    """Extracts context and knowledge from git repositories"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        try:
            self.repo = Repo(str(self.repo_path))
        except InvalidGitRepositoryError:
            raise NotAGitRepoError(f"Not a git repository: {repo_path}")
        
        # Cache for expensive operations
        self._commit_cache: Dict[str, CommitInfo] = {}
        self._file_cache: Dict[str, FileHistory] = {}
    
    def get_repo_stats(self) -> RepoStats:
        """Get overall repository statistics"""
        commits = list(self.repo.iter_commits())
        
        if not commits:
            return RepoStats(
                commit_count=0,
                file_count=0,
                contributor_count=0,
                age_days=0,
                primary_language=None,
                languages={},
                recent_activity=[],
                branch_count=len(list(self.repo.branches)),
                current_branch=self.repo.active_branch.name if self.repo.active_branch else "unknown"
            )
        
        # Basic stats
        commit_count = len(commits)
        contributors = set(commit.author.email for commit in commits)
        contributor_count = len(contributors)
        
        # Repository age
        oldest_commit = commits[-1]
        newest_commit = commits[0]
        age_days = (newest_commit.committed_date - oldest_commit.committed_date) // 86400
        
        # File analysis
        try:
            tracked_files = [item.a_path for item in self.repo.head.commit.tree.traverse() 
                           if item.type == 'blob']
            file_count = len(tracked_files)
            languages = self._analyze_languages(tracked_files)
            primary_language = max(languages.keys(), key=languages.get) if languages else None
        except:
            file_count = 0
            languages = {}
            primary_language = None
        
        # Recent activity (last 20 commits)
        recent_activity = [self._commit_to_info(commit) for commit in commits[:20]]
        
        return RepoStats(
            commit_count=commit_count,
            file_count=file_count,
            contributor_count=contributor_count,
            age_days=age_days,
            primary_language=primary_language,
            languages=languages,
            recent_activity=recent_activity,
            branch_count=len(list(self.repo.branches)),
            current_branch=self.repo.active_branch.name if self.repo.active_branch else "unknown"
        )
    
    def search_commits(self, query: str, max_results: int = 50) -> List[CommitInfo]:
        """Search commit messages and file changes for relevant commits"""
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        matching_commits = []
        
        for commit in self.repo.iter_commits():
            if len(matching_commits) >= max_results:
                break
            
            # Score based on relevance
            score = 0
            commit_text = f"{commit.message} {' '.join(commit.stats.files.keys())}".lower()
            commit_words = set(re.findall(r'\w+', commit_text))
            
            # Exact phrase match gets highest score
            if query_lower in commit_text:
                score += 10
            
            # Word overlap scoring
            word_matches = len(query_words.intersection(commit_words))
            score += word_matches * 2
            
            # File path matches
            for filepath in commit.stats.files.keys():
                if any(word in filepath.lower() for word in query_words):
                    score += 1
            
            if score > 0:
                commit_info = self._commit_to_info(commit)
                matching_commits.append((score, commit_info))
        
        # Sort by score (highest first) and return commit info
        matching_commits.sort(key=lambda x: x[0], reverse=True)
        return [commit_info for score, commit_info in matching_commits]
    
    def get_file_history(self, filepath: str) -> FileHistory:
        """Get detailed history for a specific file"""
        if filepath in self._file_cache:
            return self._file_cache[filepath]
        
        # Normalize the file path
        full_path = self.repo_path / filepath
        rel_path = str(Path(filepath).as_posix())  # Use forward slashes for git
        
        # Check if file exists
        exists = full_path.exists()
        file_size = full_path.stat().st_size if exists else None
        
        try:
            # Get commits that touched this file
            commits = list(self.repo.iter_commits(paths=rel_path))
        except git.exc.GitCommandError:
            # File might not exist in git history
            commits = []
        
        if not commits:
            history = FileHistory(
                filepath=filepath,
                exists=exists,
                creation_date=None,
                last_modified=None,
                total_commits=0,
                authors=[],
                recent_changes=[],
                lines_of_code=None,
                file_size=file_size
            )
        else:
            # File creation and modification dates
            creation_date = datetime.fromtimestamp(commits[-1].committed_date, tz=timezone.utc)
            last_modified = datetime.fromtimestamp(commits[0].committed_date, tz=timezone.utc)
            
            # Authors who worked on this file
            authors = list(set(commit.author.email for commit in commits))
            
            # Recent changes (last 10 commits)
            recent_changes = [self._commit_to_info(commit) for commit in commits[:10]]
            
            # Lines of code (if it's a text file)
            lines_of_code = None
            if exists and self._is_text_file(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines_of_code = len(f.readlines())
                except:
                    pass
            
            history = FileHistory(
                filepath=filepath,
                exists=exists,
                creation_date=creation_date,
                last_modified=last_modified,
                total_commits=len(commits),
                authors=authors,
                recent_changes=recent_changes,
                lines_of_code=lines_of_code,
                file_size=file_size
            )
        
        self._file_cache[filepath] = history
        return history
    
    def get_recent_commits(self, count: int = 20) -> List[CommitInfo]:
        """Get recent commits with details"""
        commits = list(self.repo.iter_commits())[:count]
        return [self._commit_to_info(commit) for commit in commits]
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current git state context"""
        try:
            current_branch = self.repo.active_branch.name
        except:
            current_branch = "detached"
        
        # Get current commit
        try:
            current_commit = self.repo.head.commit
            current_commit_info = self._commit_to_info(current_commit)
        except:
            current_commit_info = None
        
        # Get modified files (if any)
        try:
            modified_files = [item.a_path for item in self.repo.index.diff(None)]
            staged_files = [item.a_path for item in self.repo.index.diff("HEAD")]
        except:
            modified_files = []
            staged_files = []
        
        return {
            'branch': current_branch,
            'current_commit': current_commit_info.to_dict() if current_commit_info else None,
            'modified_files': modified_files,
            'staged_files': staged_files,
            'repo_path': str(self.repo_path)
        }
    
    def find_related_files(self, filepath: str, limit: int = 10) -> List[Tuple[str, str]]:
        """Find files related to the given file (imports, references, etc.)"""
        related = []
        
        try:
            # Look for files that import or reference this file
            file_stem = Path(filepath).stem
            
            for item in self.repo.head.commit.tree.traverse():
                if item.type != 'blob' or len(related) >= limit:
                    continue
                
                try:
                    content = item.data_stream.read().decode('utf-8', errors='ignore')
                    
                    # Simple heuristics for relationships
                    if file_stem in content:
                        # Check for imports
                        if f"import {file_stem}" in content or f"from {file_stem}" in content:
                            related.append((item.path, "imports"))
                        # Check for references
                        elif file_stem in content:
                            related.append((item.path, "references"))
                            
                except:
                    continue
                    
        except Exception:
            pass
        
        return related
    
    def analyze_complexity_trends(self) -> Dict[str, Any]:
        """Analyze how code complexity has changed over time"""
        # This is a simplified version - could be much more sophisticated
        commits = list(self.repo.iter_commits())[:100]  # Last 100 commits
        
        trends = {
            'commit_frequency': self._calculate_commit_frequency(commits),
            'file_churn': self._calculate_file_churn(commits),
            'large_commits': [c for c in commits[:20] if self._is_large_commit(c)]
        }
        
        return trends
    
    def _commit_to_info(self, commit: git.Commit) -> CommitInfo:
        """Convert git.Commit to CommitInfo dataclass"""
        if commit.hexsha in self._commit_cache:
            return self._commit_cache[commit.hexsha]
        
        # Get file changes
        try:
            files_changed = list(commit.stats.files.keys())
            insertions = commit.stats.total['insertions']
            deletions = commit.stats.total['deletions']
        except:
            files_changed = []
            insertions = 0
            deletions = 0
        
        commit_info = CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:8],
            message=commit.message.strip(),
            author=commit.author.name,
            email=commit.author.email,
            date=datetime.fromtimestamp(commit.committed_date, tz=timezone.utc),
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions
        )
        
        self._commit_cache[commit.hexsha] = commit_info
        return commit_info
    
    def _analyze_languages(self, filepaths: List[str]) -> Dict[str, int]:
        """Analyze programming languages in the repository"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.cs': 'C#',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.vue': 'Vue',
            '.jsx': 'React',
            '.tsx': 'React/TypeScript',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.yml': 'YAML', '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.md': 'Markdown',
            '.dockerfile': 'Docker'
        }
        
        languages = defaultdict(int)
        
        for filepath in filepaths:
            ext = Path(filepath).suffix.lower()
            language = language_map.get(ext, 'Other')
            languages[language] += 1
        
        return dict(languages)
    
    def _is_text_file(self, filepath: Path) -> bool:
        """Check if a file is likely a text file"""
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs',
            '.php', '.rb', '.swift', '.kt', '.scala', '.cs', '.html', '.css',
            '.scss', '.vue', '.jsx', '.tsx', '.sql', '.sh', '.yml', '.yaml',
            '.json', '.xml', '.md', '.txt', '.conf', '.cfg', '.ini'
        }
        
        return filepath.suffix.lower() in text_extensions
    
    def _calculate_commit_frequency(self, commits: List[git.Commit]) -> Dict[str, float]:
        """Calculate commit frequency metrics"""
        if len(commits) < 2:
            return {'daily_average': 0, 'weekly_average': 0}
        
        date_counts = defaultdict(int)
        for commit in commits:
            date = datetime.fromtimestamp(commit.committed_date).date()
            date_counts[date] += 1
        
        if not date_counts:
            return {'daily_average': 0, 'weekly_average': 0}
        
        total_days = (max(date_counts.keys()) - min(date_counts.keys())).days + 1
        daily_avg = len(commits) / max(total_days, 1)
        weekly_avg = daily_avg * 7
        
        return {
            'daily_average': round(daily_avg, 2),
            'weekly_average': round(weekly_avg, 2)
        }
    
    def _calculate_file_churn(self, commits: List[git.Commit]) -> Dict[str, int]:
        """Calculate which files change most frequently"""
        file_changes = defaultdict(int)
        
        for commit in commits:
            try:
                for filepath in commit.stats.files.keys():
                    file_changes[filepath] += 1
            except:
                continue
        
        # Return top 10 most changed files
        sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_files[:10])
    
    def _is_large_commit(self, commit: git.Commit) -> bool:
        """Check if a commit is unusually large"""
        try:
            total_changes = commit.stats.total['insertions'] + commit.stats.total['deletions']
            file_count = len(commit.stats.files)
            
            # Consider large if >500 lines changed or >20 files
            return total_changes > 500 or file_count > 20
        except:
            return False