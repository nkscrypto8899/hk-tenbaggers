"""
十倍股量化選股系統
=================
根據 6 個核心準則篩選具備十倍股潛質嘅股票

Author: Ape 仔
"""

import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
import logging

from settings import Settings

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StockScore:
    """單支股票評分結果"""
    symbol: str
    name: str
    
    # 原始數據
    market_cap: float = 0.0
    book_to_market: float = 0.0
    roa: float = 0.0
    ebitda: float = 0.0
    fcf_yield: float = 0.0
    price_to_52w_low: float = 0.0
    asset_growth: float = 0.0
    earnings_growth: float = 0.0
    beta: float = 1.0
    current_price: float = 0.0
    
    # 各項分數
    market_cap_score: float = 0.0
    value_score: float = 0.0
    cash_flow_score: float = 0.0
    price_position_score: float = 0.0
    balance_score: float = 0.0
    rate_sensitivity_score: float = 0.0
    
    # 總分
    total_score: float = 0.0
    
    # 中間數值用於比較
    industry_median_btm: float = 0.0
    industry_median_fcf: float = 0.0


class ScoringEngine:
    """
    評分引擎
    根據 6 個準則為股票打分
    """
    
    def __init__(self, config: Settings):
        self.config = config
        self.weights = config.weights
    
    def calculate_market_cap_score(self, stock: StockScore) -> float:
        """
        準則1: 初始市值要細
        市值 < $2.5億 = 100分, > $10億 = 0分
        """
        cap = stock.market_cap
        
        if cap <= 0:
            return 0.0
        
        max_cap = self.config.market_cap_max  # 2.5億
        min_cap = self.config.market_cap_min  # 1000萬
        
        # 越小分數越高
        if cap <= min_cap:
            return 100.0
        elif cap >= max_cap:
            return 0.0
        else:
            # 線性插值
            score = 100 * (max_cap - cap) / (max_cap - min_cap)
            return max(0, min(100, score))
    
    def calculate_value_score(self, stock: StockScore) -> float:
        """
        準則2: 高價值與高獲利能力
        Book-to-Market + ROA + EBITDA 综合评分
        """
        scores = []
        
        # Book-to-Market (越高越好,表示價值型)
        # 行業中位數標準化
        if stock.industry_median_btm > 0:
            btm_ratio = stock.book_to_market / stock.industry_median_btm
            scores.append(min(100, btm_ratio * 50))  # 50為基礎分
        
        # ROA (越高越好)
        if stock.roa > 0:
            scores.append(min(100, stock.roa * 10))  # ROA 10% = 100分
        
        # EBITDA (相對值)
        if stock.ebitda > 0:
            scores.append(min(100, stock.ebitda * 5))  # 簡化計算
        
        if not scores:
            return 50.0  # 預設分
        
        return sum(scores) / len(scores)
    
    def calculate_cash_flow_score(self, stock: StockScore) -> float:
        """
        準則3: 強勁現金流
        FCF Yield 越高分數越高
        """
        fcf = stock.fcf_yield
        
        if fcf <= 0:
            return 0.0
        
        # FCF Yield > 10% = 100分
        score = min(100, fcf * 10)
        return score
    
    def calculate_price_position_score(self, stock: StockScore) -> float:
        """
        準則4: 低位入場
        股價接近 12 個月低位分數高
        """
        ratio = stock.price_to_52w_low
        
        if ratio <= 0:
            return 50.0
        
        # ratio = current_price / 52w_low
        # ratio 越接近 1 = 越低位 = 分數越高
        
        # 1.0 = 100分, 1.5 = 0分
        if ratio <= 1.0:
            return 100.0
        elif ratio >= 1.5:
            return 0.0
        else:
            return 100 * (1.5 - ratio) / 0.5
    
    def calculate_balance_score(self, stock: StockScore) -> float:
        """
        準則5: 資產擴張速度嘅平衡
        資產增速 < 盈餘增速 = 分數高
        """
        asset_g = stock.asset_growth
        earn_g = stock.earnings_growth
        
        # 兩者都應該是正數但不要差太遠
        if asset_g <= 0 and earn_g <= 0:
            return 50.0
        
        if earn_g <= 0:
            return 20.0  # 盈利負增長，分數低
        
        if asset_g <= 0:
            return 80.0  # 資產收縮但盈利正增長，好
        
        ratio = asset_g / earn_g
        
        # ratio < 1 = 資產增速低過盈利增速 = 好 = 100分
        # ratio = 1 = 平衡 = 70分
        # ratio > 2 = 資產擴張太快 = 差 = 30分
        if ratio <= 0.5:
            return 100.0
        elif ratio <= 1.0:
            return 80.0
        elif ratio <= 1.5:
            return 60.0
        elif ratio <= 2.0:
            return 40.0
        else:
            return 20.0
    
    def calculate_rate_sensitivity_score(self, stock: StockScore) -> float:
        """
        準則6: 利率敏感度
        Beta 越高分數越高
        """
        beta = stock.beta
        
        # Beta > 1.5 = 100分, Beta = 1.0 = 50分, Beta < 0.5 = 0分
        if beta >= 1.5:
            return 100.0
        elif beta <= 0.5:
            return 0.0
        else:
            return (beta - 0.5) / 1.0 * 100
    
    def calculate_total_score(self, stock: StockScore) -> float:
        """計算總分"""
        stock.market_cap_score = self.calculate_market_cap_score(stock)
        stock.value_score = self.calculate_value_score(stock)
        stock.cash_flow_score = self.calculate_cash_flow_score(stock)
        stock.price_position_score = self.calculate_price_position_score(stock)
        stock.balance_score = self.calculate_balance_score(stock)
        stock.rate_sensitivity_score = self.calculate_rate_sensitivity_score(stock)
        
        # 加權總分
        total = (
            stock.market_cap_score * self.weights['market_cap'] +
            stock.value_score * self.weights['value'] +
            stock.cash_flow_score * self.weights['cash_flow'] +
            stock.price_position_score * self.weights['price_position'] +
            stock.balance_score * self.weights['balance'] +
            stock.rate_sensitivity_score * self.weights['rate_sensitivity']
        )
        
        stock.total_score = total
        return total


def demo():
    """演示：創建虛構股票測試評分"""
    settings = Settings()
    engine = ScoringEngine(settings)
    
    # 測試股票：模擬一間小型價值股
    stock = StockScore(
        symbol="DEMO",
        name="Demo Company",
        market_cap=150_000_000,  # $1.5億，符合 < $2.5億
        book_to_market=0.8,
        roa=0.12,  # 12% ROA
        ebitda=0.25,
        fcf_yield=0.08,  # 8% FCF Yield
        price_to_52w_low=1.05,  # 接近52週低位
        asset_growth=0.10,  # 10% 資產增長
        earnings_growth=0.20,  # 20% 盈利增長
        beta=1.8,  # 高Beta
        industry_median_btm=0.5,
        industry_median_fcf=0.05
    )
    
    score = engine.calculate_total_score(stock)
    
    print("=" * 60)
    print(f"🎯 測試股票: {stock.name} ({stock.symbol})")
    print("=" * 60)
    print(f"總評分: {score:.2f} / 100")
    print("-" * 60)
    print(f"各項分數:")
    print(f"  1. 市值分 (初始市值要細):      {stock.market_cap_score:.1f}")
    print(f"  2. 價值分 (高價值+高獲利):     {stock.value_score:.1f}")
    print(f"  3. 現金流分 (強勁現金流):      {stock.cash_flow_score:.1f}")
    print(f"  4. 低位分 (低位入場):          {stock.price_position_score:.1f}")
    print(f"  5. 平衡分 (資產/盈餘平衡):    {stock.balance_score:.1f}")
    print(f"  6. 利率敏感度分:              {stock.rate_sensitivity_score:.1f}")
    print("=" * 60)
    
    # 評語
    if score >= 70:
        print("✅ 極具十倍股潛質！")
    elif score >= 55:
        print("👍 具備一定十倍股特質")
    elif score >= 40:
        print("⚠️ 中等潛質，部分指標合格")
    else:
        print("❌ 不太符合十倍股標準")
    
    return stock


if __name__ == "__main__":
    demo()
