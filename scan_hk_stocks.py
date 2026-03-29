#!/usr/bin/env python3
"""
港股主板完整清單掃描器
======================
自動掃描 0001-9999 所有港股主板代碼
保存為 CSV 文件

使用方法:
    python scan_hk_stocks.py

Author: Ape 仔
"""

import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime
import sys

# 配置
BATCH_SIZE = 50      # 每批檢測數量
DELAY = 0.15          # 每個請求延遲 (秒) - 避免被限流
OUTPUT_FILE = "hk_stocks_master.csv"
LOG_FILE = "scan_log.txt"

# 股票類型過濾
EXCLUDED_BOARDS = ['GEM', 'CBBC', 'DWs', 'Inline Warrants', 'REITs']


def check_stock(code: str) -> dict:
    """檢查股票是否存在並返回基本資訊"""
    symbol = f"{code}.HK"
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 檢查是否有有效數據
        if info.get('regularMarketPrice') and info.get('marketCap'):
            return {
                'code': code,
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', 'N/A')),
                'current_price': info.get('regularMarketPrice'),
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'stock_exchange': info.get('exchange', 'HKEX'),
                'market': info.get('market', 'N/A'),
                'currency': info.get('currency', 'HKD'),
                'beta': info.get('beta', 1.0),
                'price_to_book': info.get('priceToBook', 0),
                'return_on_assets': info.get('returnOnAssets', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'free_cashflow': info.get('freeCashflow', 0),
                '52w_low': info.get('fiftyTwoWeekLow', 0),
                '52w_high': info.get('fiftyTwoWeekHigh', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'is_valid': True
            }
    except Exception as e:
        pass
    
    return None


def scan_range(start: int, end: int, progress_callback=None) -> list:
    """掃描指定範圍的股票"""
    results = []
    total = end - start + 1
    
    for i in range(start, end + 1):
        code = str(i).zfill(4)
        result = check_stock(code)
        
        if result:
            results.append(result)
        
        # 進度顯示
        if i % 10 == 0:
            progress = (i - start + 1) / total * 100
            print(f"  進度: {progress:.1f}% ({i - start + 1}/{total}) - 已找到 {len(results)} 支")
            if progress_callback:
                progress_callback(progress)
        
        time.sleep(DELAY)
    
    return results


def save_results(results: list):
    """保存結果到 CSV"""
    if not results:
        print("⚠️ 沒有結果可保存")
        return
    
    df = pd.DataFrame(results)
    
    # 排序
    df = df.sort_values('code')
    
    # 保存
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ 已保存到 {OUTPUT_FILE}")
    print(f"   總股票數量: {len(df)}")


def main():
    print("=" * 60)
    print("🐵 港股主板完整清單掃描器")
    print("=" * 60)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"輸出文件: {OUTPUT_FILE}")
    print()
    
    # 檢查現有文件
    existing_count = 0
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_csv(OUTPUT_FILE)
            existing_count = len(existing_df)
            print(f"📖 現有文件包含 {existing_count} 支股票")
        except:
            pass
    
    print(f"\n🔍 開始掃描 HKEX 主板股票...")
    print(f"   範圍: 0001 - 9999")
    print(f"   預計時間: 20-40 分鐘 (取決於網絡)")
    print(f"   請耐心等待...\n")
    
    # 分段掃描以便追蹤進度
    ranges = [
        (1, 999),      # 001-0999
        (1000, 1999),  # 1000-1999
        (2000, 2999),  # 2000-2999
        (3000, 3999),  # 3000-3999 (GEM範圍)
        (4000, 4999),  # 4000-4999
        (5000, 5999),  # 5000-5999
        (6000, 6999),  # 6000-6999
        (7000, 7999),  # 7000-7999
        (8000, 8999),  # 8000-8999
        (9000, 9999),  # 9000-9999
    ]
    
    all_results = []
    total_start = time.time()
    
    for idx, (start, end) in enumerate(ranges):
        print(f"\n📊 [{idx+1}/{len(ranges)}] 掃描 {start:04d} - {end:04d}...")
        range_start = time.time()
        
        results = scan_range(start, end)
        
        range_time = time.time() - range_start
        print(f"   完成！找到 {len(results)} 支股票，耗時 {range_time:.1f}秒")
        
        all_results.extend(results)
        
        # 顯示即時統計
        total_time = time.time() - total_start
        print(f"   累計: {len(all_results)} 支股票，總耗時 {total_time/60:.1f}分鐘")
    
    # 保存結果
    print()
    print("=" * 60)
    print("💾 保存結果...")
    save_results(all_results)
    
    total_time = time.time() - total_start
    print()
    print("=" * 60)
    print(f"✅ 掃描完成！")
    print(f"   總股票數量: {len(all_results)}")
    print(f"   總耗時: {total_time/60:.1f} 分鐘")
    print("=" * 60)
    
    # 顯示前20支
    if all_results:
        print("\n📋 前20支股票:")
        df = pd.DataFrame(all_results)
        print(df[['code', 'name', 'sector']].head(20).to_string(index=False))
    
    return all_results


if __name__ == "__main__":
    results = main()
