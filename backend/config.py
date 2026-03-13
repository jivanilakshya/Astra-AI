"""
Astra-AI Configuration Manager
Handles loading and validating configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Central configuration manager for Astra-AI system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config.yaml file. Defaults to ./config/config.yaml
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Set config path
        if config_path is None:
            self.config_path = Path(__file__).parent / "config" / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        # Load configuration
        self.config = self._load_config()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _apply_env_overrides(self):
        """Override configuration with environment variables."""
        # Model settings
        if os.getenv("DEFAULT_GENERATOR_MODEL"):
            provider, model = self._parse_model_string(os.getenv("DEFAULT_GENERATOR_MODEL"))
            self.config['models']['generator']['provider'] = provider
            self.config['models']['generator']['model_name'] = model
        
        if os.getenv("DEFAULT_JUDGE_MODEL"):
            provider, model = self._parse_model_string(os.getenv("DEFAULT_JUDGE_MODEL"))
            self.config['models']['judge']['provider'] = provider
            self.config['models']['judge']['model_name'] = model
        
        # Ollama settings
        if os.getenv("OLLAMA_BASE_URL"):
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        else:
            self.ollama_base_url = "http://localhost:11434"
        
        # HuggingFace settings
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        # DSPy settings (optional - section may be commented out)
        if os.getenv("DSPY_CACHE_DIR") and 'dspy' in self.config:
            self.config['dspy']['cache_dir'] = os.getenv("DSPY_CACHE_DIR")
        
        if os.getenv("DSPY_MAX_TOKENS"):
            self.config['models']['generator']['max_tokens'] = int(os.getenv("DSPY_MAX_TOKENS"))
        
        if os.getenv("DSPY_TEMPERATURE"):
            self.config['models']['generator']['temperature'] = float(os.getenv("DSPY_TEMPERATURE"))
        
        # Optimization settings
        if os.getenv("MAX_ITERATIONS"):
            self.config['optimization']['max_iterations'] = int(os.getenv("MAX_ITERATIONS"))
        
        if os.getenv("CONVERGENCE_THRESHOLD"):
            self.config['optimization']['convergence_threshold'] = float(os.getenv("CONVERGENCE_THRESHOLD"))
        
        # Evaluation weights
        if os.getenv("WEIGHT_CORRECTNESS"):
            self.config['evaluation']['weights']['correctness'] = float(os.getenv("WEIGHT_CORRECTNESS"))
        if os.getenv("WEIGHT_CLARITY"):
            self.config['evaluation']['weights']['clarity'] = float(os.getenv("WEIGHT_CLARITY"))
        if os.getenv("WEIGHT_REASONING"):
            self.config['evaluation']['weights']['reasoning'] = float(os.getenv("WEIGHT_REASONING"))
        if os.getenv("WEIGHT_RELEVANCE"):
            self.config['evaluation']['weights']['relevance'] = float(os.getenv("WEIGHT_RELEVANCE"))
        if os.getenv("WEIGHT_CONCISENESS"):
            self.config['evaluation']['weights']['conciseness'] = float(os.getenv("WEIGHT_CONCISENESS"))
        
        # Logging settings
        if os.getenv("LOG_LEVEL"):
            self.config['logging']['level'] = os.getenv("LOG_LEVEL")
        
        if os.getenv("LOG_DIR"):
            self.config['logging']['log_dir'] = os.getenv("LOG_DIR")
    
    def _parse_model_string(self, model_string: str) -> tuple:
        """
        Parse model string in format 'provider/model_name'.
        
        Args:
            model_string: String like 'ollama/llama3.1'
        
        Returns:
            Tuple of (provider, model_name)
        """
        if '/' in model_string:
            provider, model_name = model_string.split('/', 1)
            return provider, model_name
        else:
            # Default to ollama if no provider specified
            return 'ollama', model_string
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate evaluation weights sum to 1.0
        weights = self.config['evaluation']['weights']
        total_weight = sum(weights.values())
        
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(
                f"Evaluation weights must sum to 1.0, got {total_weight:.2f}. "
                f"Weights: {weights}"
            )
        
        # Validate convergence threshold
        threshold = self.config['optimization']['convergence_threshold']
        if not (0 <= threshold <= 10):
            raise ValueError(
                f"Convergence threshold must be between 0 and 10, got {threshold}"
            )
        
        # Validate max iterations
        max_iter = self.config['optimization']['max_iterations']
        if max_iter < 1:
            raise ValueError(f"Max iterations must be at least 1, got {max_iter}")
    
    # Convenience property accessors
    @property
    def generator_model(self) -> Dict[str, Any]:
        """Get generator model configuration."""
        return self.config['models']['generator']
    
    @property
    def judge_model(self) -> Dict[str, Any]:
        """Get judge model configuration."""
        return self.config['models']['judge']
    
    @property
    def optimizer_model(self) -> Dict[str, Any]:
        """Get optimizer model configuration."""
        return self.config['models']['optimizer']
    
    @property
    def evaluation_weights(self) -> Dict[str, float]:
        """Get evaluation criteria weights."""
        return self.config['evaluation']['weights']
    
    @property
    def max_iterations(self) -> int:
        """Get maximum optimization iterations."""
        return self.config['optimization']['max_iterations']
    
    @property
    def convergence_threshold(self) -> float:
        """Get convergence threshold."""
        return self.config['optimization']['convergence_threshold']
    
    @property
    def dspy_config(self) -> Dict[str, Any]:
        """Get DSPy configuration."""
        return self.config['dspy']
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config['logging']
    
    @property
    def data_config(self) -> Dict[str, Any]:
        """Get data configuration."""
        return self.config['data']
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path like 'models.generator.temperature'
            default: Default value if key not found
        
        Returns:
            Configuration value
        
        Example:
            >>> config.get('models.generator.temperature')
            0.7
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config(config_path={self.config_path})"


# Global config instance
_config_instance = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_path)
    
    return _config_instance


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = get_config()
    
    print("=== Astra-AI Configuration ===")
    print(f"\nGenerator Model: {config.generator_model}")
    print(f"Judge Model: {config.judge_model}")
    print(f"Evaluation Weights: {config.evaluation_weights}")
    print(f"Max Iterations: {config.max_iterations}")
    print(f"Convergence Threshold: {config.convergence_threshold}")
    print(f"\nDSPy Config: {config.dspy_config}")
