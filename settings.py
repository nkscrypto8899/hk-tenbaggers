"""
系統配置模組
============

Author: Ape 仔
"""

import os
import yaml
from dataclasses import dataclass


class Settings:
    """系統配置"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                'settings.yaml'
            )
        
        with open(config_path, 'r') as f:
            self._raw = yaml.safe_load(f)
        
        self.stock_picker = self._raw.get('stock_picker', {})
        self.telegram = self._raw.get('telegram', {})
        self.scheduler = self._raw.get('scheduler', {})
        self.backtest = self._raw.get('backtest', {})
    
    @property
    def market_cap_max(self) -> float:
        return self.stock_picker.get('market_cap', {}).get('max', 250_000_000)
    
    @property
    def market_cap_min(self) -> float:
        return self.stock_picker.get('market_cap', {}).get('min', 10_000_000)
    
    @property
    def weights(self) -> dict:
        return self.stock_picker.get('weights', {
            'market_cap': 0.1667,
            'value': 0.1667,
            'cash_flow': 0.1667,
            'price_position': 0.1667,
            'balance': 0.1667,
            'rate_sensitivity': 0.1667,
        })
    
    def get_env(self, key: str, default: str = None) -> str:
        return os.environ.get(key, default)


# 移除 scoring_engine.py 入面重複嘅 Config class
# 統一使用 settings.py
