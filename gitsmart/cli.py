"""
GitSmart CLI - Command line interface for repository intelligence
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .core import GitSmart
from .exceptions import GitSmartError, NotAGitRepoError, APIKeyMissingError
from .config import Config


console = Console()


def find_git_root() -> Optional[Path]:
    """Find the root of the git repository"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    return None


def ensure_git_repo() -> Path:
    """Ensure we're in a git repository"""
    git_root = find_git_root()
    if not git_root:
        console.print("❌ Error: Not in a git repository", style="red")
        console.print("💡 Run this command from inside a git repository", style="yellow")
        sys.exit(1)
    return git_root


def handle_error(error: Exception):
    """Handle errors with user-friendly messages"""
    if isinstance(error, NotAGitRepoError):
        console.print("❌ Error: Not in a git repository", style="red")
        console.print("💡 Run this command from inside a git repository", style="yellow")
    elif isinstance(error, APIKeyMissingError):
        console.print("❌ Error: OpenAI API key not configured", style="red") 
        console.print("💡 Run `gitsmart init` to set up your API key", style="yellow")
    elif isinstance(error, GitSmartError):
        console.print(f"❌ Error: {error}", style="red")
    else:
        console.print(f"❌ Unexpected error: {error}", style="red")
        console.print("💡 Please report this issue at https://github.com/gitsmart/gitsmart/issues", style="yellow")
    sys.exit(1)


@click.group()
@click.version_option(version="0.1.0", prog_name="GitSmart")
@click.option("--repo", type=click.Path(exists=True), help="Path to git repository")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output")
@click.pass_context
def cli(ctx, repo, verbose, quiet):
    """GitSmart: Your git repository's memory made searchable
    
    Ask questions about your codebase, understand file evolution,
    and remember decisions with full context.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if repo:
        os.chdir(repo)


@cli.command()
@click.argument("question")
@click.option("--format", type=click.Choice(["plain", "business", "json"]), 
              default="plain", help="Output format")
@click.option("--context", type=int, default=100, help="Number of commits to analyze")
@click.option("--include-impact", is_flag=True, help="Include business impact analysis")
@click.pass_context  
def ask(ctx, question, format, context, include_impact):
    """Ask questions about your repository
    
    Examples:
      gitsmart ask "Why do we use Redis?"
      gitsmart ask "What is this repository about?"
      gitsmart ask "When was authentication added?"
    """
    try:
        repo_path = ensure_git_repo()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=ctx.obj.get('quiet', False)
        ) as progress:
            task = progress.add_task("🔍 Analyzing repository history...", total=None)
            
            gitsmart = GitSmart(repo_path)
            answer = gitsmart.ask(
                question, 
                max_commits=context,
                output_format=format,
                include_impact=include_impact
            )
            
            progress.remove_task(task)
        
        if format == "json":
            console.print_json(answer)
        else:
            console.print(Panel(answer, title="🤖 GitSmart Answer", border_style="blue"))
            
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("path", default=".")
@click.option("--history", is_flag=True, help="Include full evolution history")
@click.option("--usage", is_flag=True, help="Show where/how file is used")
@click.option("--include-impact", is_flag=True, help="Include business impact")
@click.pass_context
def explain(ctx, path, history, usage, include_impact):
    """Explain why files or directories exist
    
    Examples:
      gitsmart explain app.py
      gitsmart explain src/components/
      gitsmart explain .
    """
    try:
        repo_path = ensure_git_repo()
        
        with Progress(
            SpinnerColumn(), 
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=ctx.obj.get('quiet', False)
        ) as progress:
            task = progress.add_task(f"📄 Analyzing {path}...", total=None)
            
            gitsmart = GitSmart(repo_path)
            explanation = gitsmart.explain(
                path,
                include_history=history,
                include_usage=usage,
                include_impact=include_impact
            )
            
            progress.remove_task(task)
        
        console.print(Panel(explanation, title=f"📖 Explanation: {path}", border_style="green"))
        
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("decision")
@click.option("--type", type=click.Choice(["decision", "note", "bug", "meeting"]), 
              default="decision", help="Type of memory")
@click.option("--tag", multiple=True, help="Tags for categorization")
@click.pass_context
def remember(ctx, decision, type, tag):
    """Store decisions and notes with git context
    
    Examples:
      gitsmart remember "Decided to use PostgreSQL over MongoDB"  
      gitsmart remember "Bug in auth flow - investigate timeout" --type=bug
      gitsmart remember "Team meeting: API v2 launch in March" --type=meeting
    """
    try:
        repo_path = ensure_git_repo()
        
        gitsmart = GitSmart(repo_path)
        memory_id = gitsmart.remember(decision, memory_type=type, tags=list(tag))
        
        console.print("💾 Saved decision with context:", style="green")
        console.print(f"   Content: {decision}")
        console.print(f"   ID: {memory_id}")
        console.print(f"   Type: {type}")
        if tag:
            console.print(f"   Tags: {', '.join(tag)}")
            
        console.print("\n💡 This decision will be included in future queries", style="yellow")
        
    except Exception as e:
        handle_error(e)


@cli.command()
@click.option("--provider", type=click.Choice(["deepseek", "openai", "anthropic"]), 
              default="deepseek", help="AI provider")
@click.option("--api-key", help="API key (or set DEEPSEEK_API_KEY/OPENAI_API_KEY env var)")
@click.option("--model", help="AI model to use")
def init(provider, api_key, model):
    """Initialize GitSmart in this repository"""
    try:
        repo_path = ensure_git_repo()
        
        console.print("🚀 Setting up GitSmart in this repository...\n")
        
        # Check git repository
        gitsmart = GitSmart(repo_path)
        stats = gitsmart.get_repo_stats()
        
        console.print(f"✓ Git repository detected: {repo_path}")
        console.print(f"✓ {stats['commit_count']} commits found")
        
        if stats['commit_count'] == 0:
            console.print("⚠️  Repository has no commits yet", style="yellow")
            console.print("   GitSmart works best with some git history", style="yellow")
        
        # Set up configuration
        config = Config(repo_path)
        
        # Set provider first so we can check for the right API key
        config.set('ai.provider', provider)
        
        # Check if API key is available from environment after Config loads env
        if not api_key:
            ai_config = config.get_ai_config()
            api_key = ai_config.get('api_key')
        
        if not api_key:
            provider_name = provider.upper()
            api_key = click.prompt(f"\n🔑 Enter your {provider_name} API key", hide_input=True)
        
        config.set_ai_config(provider=provider, api_key=api_key, model=model)
        
        # Test API connection
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🧪 Testing AI connection...", total=None)
            
            try:
                test_response = gitsmart.test_ai_connection()
                progress.remove_task(task)
                console.print("✓ AI connection successful")
            except Exception as e:
                progress.remove_task(task)
                console.print(f"❌ AI connection failed: {e}", style="red")
                raise
        
        console.print("\n🎉 GitSmart is ready! Try these commands:")
        console.print("  gitsmart ask \"What is this repository about?\"")
        console.print("  gitsmart explain README.md")
        console.print("  gitsmart remember \"Initial setup complete\"")
        
    except Exception as e:
        handle_error(e)


@cli.command()
@click.option("--verbose", is_flag=True, help="Show detailed status")
def status(verbose):
    """Show GitSmart status and statistics"""
    try:
        repo_path = ensure_git_repo()
        
        gitsmart = GitSmart(repo_path)
        status_info = gitsmart.get_status()
        
        console.print("📊 GitSmart Status\n")
        
        # Repository info
        console.print("[bold]Repository:[/bold]")
        console.print(f"  • Path: {repo_path}")
        console.print(f"  • Commits: {status_info['repo']['commit_count']}")
        console.print(f"  • Files tracked: {status_info['repo']['file_count']}")
        console.print(f"  • Current branch: {status_info['repo']['current_branch']}")
        
        # Configuration
        console.print(f"\n[bold]Configuration:[/bold]")  
        console.print(f"  • AI Provider: {status_info['config']['ai_provider']}")
        console.print(f"  • Model: {status_info['config']['ai_model']}")
        console.print(f"  • API Key: {'✓ Configured' if status_info['config']['api_key_configured'] else '❌ Missing'}")
        
        # Knowledge base
        console.print(f"\n[bold]Knowledge Base:[/bold]")
        console.print(f"  • Decisions stored: {status_info['knowledge']['decision_count']}")
        console.print(f"  • Last activity: {status_info['knowledge']['last_activity']}")
        console.print(f"  • Cache size: {status_info['knowledge']['cache_size']}")
        
        if verbose:
            console.print(f"\n[bold]Recent Decisions:[/bold]")
            for decision in status_info['knowledge']['recent_decisions'][:5]:
                console.print(f"  • {decision}")
        
        console.print("\n💡 Use `gitsmart ask \"summarize recent changes\"` for update overview")
        
    except Exception as e:
        handle_error(e)


@cli.command("config") 
@click.argument("action", type=click.Choice(["list", "get", "set"]))
@click.argument("key", required=False)
@click.argument("value", required=False)
def config_cmd(action, key, value):
    """Manage GitSmart configuration
    
    Examples:
      gitsmart config list
      gitsmart config get ai.provider
      gitsmart config set ai.model gpt-3.5-turbo
    """
    try:
        repo_path = ensure_git_repo()
        config = Config(repo_path)
        
        if action == "list":
            config_data = config.get_all()
            console.print("⚙️  GitSmart Configuration:\n")
            for section, values in config_data.items():
                console.print(f"[bold]{section}:[/bold]")
                for k, v in values.items():
                    if "key" in k.lower() and v:
                        v = "***hidden***"
                    console.print(f"  {k}: {v}")
                console.print()
                
        elif action == "get":
            if not key:
                raise click.UsageError("Key is required for 'get' action")
            value = config.get(key)
            console.print(f"{key}: {value}")
            
        elif action == "set":
            if not key or not value:
                raise click.UsageError("Both key and value are required for 'set' action")
            config.set(key, value)
            console.print(f"✓ Set {key} = {value}")
            
    except Exception as e:
        handle_error(e)


@cli.command("analyze-commit")
@click.argument("commit_hash")
@click.option("--suggest-only", is_flag=True, help="Only suggest reasoning, don't store")
def analyze_commit(commit_hash, suggest_only):
    """Analyze a commit and suggest reasoning for the changes"""
    try:
        repo_path = ensure_git_repo()
        gitsmart = GitSmart(repo_path)
        
        # Get commit details
        commit_info = gitsmart.git_extractor.repo.commit(commit_hash)
        
        # Build context for AI analysis
        context = {
            'commit_hash': commit_hash,
            'commit_message': commit_info.message.strip(),
            'files_changed': list(commit_info.stats.files.keys()),
            'lines_added': commit_info.stats.total['insertions'],
            'lines_deleted': commit_info.stats.total['deletions'],
            'author': commit_info.author.name,
            'date': commit_info.committed_datetime.isoformat()
        }
        
        # Use AI to analyze the commit and suggest reasoning
        ai_service = gitsmart._get_ai_service()
        
        prompt = f"""Analyze this git commit and suggest concise reasoning for why this change was made:

Commit: {commit_hash}
Message: {commit_info.message.strip()}
Files changed: {', '.join(context['files_changed'][:10])}
Lines: +{context['lines_added']} -{context['lines_deleted']}

Provide a 1-2 sentence explanation of the likely reasoning behind this change. Focus on the "why" not the "what"."""
        
        # Create a simple AI request (not using full repository context)
        from openai import OpenAI
        import os
        
        # Try to get AI analysis
        try:
            api_key = gitsmart.config.get_ai_config().get('api_key')
            provider = gitsmart.config.get_ai_config().get('provider', 'deepseek')
            
            if provider == 'deepseek':
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                model = "deepseek-chat"
            else:
                client = OpenAI(api_key=api_key)
                model = "gpt-3.5-turbo"
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            reasoning = response.choices[0].message.content.strip()
            
        except Exception:
            # Fallback to commit message analysis
            reasoning = f"Implemented changes related to: {commit_info.message.strip()}"
        
        if suggest_only:
            console.print(reasoning)
        else:
            # Store as memory
            memory_id = gitsmart.remember(reasoning, memory_type="decision", tags=["auto-analyzed"])
            console.print(f"✅ Analyzed and stored: {reasoning}")
            console.print(f"Memory ID: {memory_id}")
        
    except Exception as e:
        handle_error(e)


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()