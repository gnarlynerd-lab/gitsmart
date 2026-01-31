"""
Configuration Management - Handles GitSmart settings and preferences
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from .exceptions import ConfigurationError


class Config:
    """Manages GitSmart configuration"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.gitsmart_dir = self.repo_path / ".gitsmart"
        self.config_file = self.gitsmart_dir / "config.yml"
        
        # Load environment variables from .env files
        # First check repo root, then gitsmart-src directory (for development)
        env_files = [
            self.repo_path / ".env",
            self.repo_path / "gitsmart-dev" / "gitsmart-src" / ".env"
        ]
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                break
        
        # Ensure .gitsmart directory exists
        self.gitsmart_dir.mkdir(exist_ok=True)
        
        # Default configuration
        self.defaults = {
            'ai': {
                'provider': os.getenv('DEFAULT_AI_PROVIDER', 'deepseek'),
                'model': None,  # Will be set based on provider
                'temperature': 0.7,
                'max_tokens': 2000
            },
            'storage': {
                'max_cache_size': '100MB',
                'cache_ttl_days': 30
            },
            'output': {
                'format': 'plain',
                'color': True,
                'verbose': False
            }
        }
        
        # Load existing config or create default
        self._config = self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'ai.provider')"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save configuration
        self._save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration"""
        return self._config.copy()
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration with environment variables"""
        ai_config = self._config.get('ai', {}).copy()
        
        # Get API key from environment
        provider = ai_config.get('provider', 'deepseek')
        
        if provider == 'deepseek':
            api_key = os.getenv('DEEPSEEK_API_KEY')
            default_model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            default_model = os.getenv('OPENAI_MODEL', 'gpt-4')
        else:
            api_key = None
            default_model = None
        
        ai_config['api_key'] = api_key
        
        # Set model if not specified
        if not ai_config.get('model'):
            ai_config['model'] = default_model
        
        return ai_config
    
    def set_ai_config(
        self, 
        provider: str, 
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> None:
        """Set AI configuration and optionally store API key in environment"""
        
        # Update config
        self.set('ai.provider', provider)
        
        if model:
            self.set('ai.model', model)
        
        # Store API key in environment variable (for this session)
        if api_key:
            if provider == 'deepseek':
                os.environ['DEEPSEEK_API_KEY'] = api_key
            elif provider == 'openai':
                os.environ['OPENAI_API_KEY'] = api_key
        
        # Save to .env file for persistence
        if api_key:
            self._update_env_file(provider, api_key)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
                
                # Merge with defaults
                merged_config = self._merge_configs(self.defaults, config)
                return merged_config
                
            except Exception as e:
                raise ConfigurationError(f"Failed to load config: {e}")
        else:
            # Create default config file
            self._save_config(self.defaults)
            return self.defaults.copy()
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file"""
        config = config or self._config
        
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    def _merge_configs(self, defaults: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with defaults"""
        merged = defaults.copy()
        
        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _update_env_file(self, provider: str, api_key: str) -> None:
        """Update .env file with API key"""
        env_file = self.repo_path / ".env"
        
        # Read existing .env if it exists
        env_lines = []
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    env_lines = f.readlines()
            except Exception:
                pass
        
        # Determine which key to update
        key_name = f"{provider.upper()}_API_KEY"
        key_line = f"{key_name}={api_key}\n"
        
        # Update or add the key
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{key_name}="):
                env_lines[i] = key_line
                updated = True
                break
        
        if not updated:
            env_lines.append(key_line)
        
        # Write back to .env
        try:
            with open(env_file, 'w') as f:
                f.writelines(env_lines)
        except Exception as e:
            # If we can't write .env, at least the environment variable is set for this session
            pass