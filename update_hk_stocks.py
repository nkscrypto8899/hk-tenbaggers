"""
港股代碼更新腳本
================
自動掃描並更新港股代碼列表

使用方法:
    python update_hk_stocks.py

Author: Ape 仔
"""

import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime

# HK stock codes range: 0001 - 9999 (main board)
# HKEX main board has ~2500 stocks

BATCH_SIZE = 50  # 每批檢測數量
DELAY = 0.1  # 每個請求延遲 (秒)
OUTPUT_FILE = "hk_stocks_master.csv"
LOG_FILE = "update_log.txt"


def check_stock(symbol: str) -> dict:
    """檢查股票是否存在並返回基本資訊"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 檢查是否有有效數據
        if info.get('regularMarketPrice') and info.get('marketCap'):
            return {
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', 'N/A')),
                'code': symbol.replace('.HK', ''),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'exchange': 'HKEX',
                'market': 'Main Board',
                'valid': True
            }
    except Exception:
        pass
    
    return None


def scan_range(start: int, end: int, progress_callback=None) -> list:
    """掃描指定範圍的股票"""
    results = []
    total = end - start + 1
    
    for i in range(start, end + 1):
        code = str(i).zfill(4)
        symbol = f"{code}.HK"
        
        result = check_stock(symbol)
        
        if result:
            results.append(result)
        
        if i % BATCH_SIZE == 0:
            progress = (i - start + 1) / total * 100
            print(f"  進度: {progress:.1f}% ({i - start + 1}/{total})")
            if progress_callback:
                progress_callback(progress)
        
        time.sleep(DELAY)
    
    return results


def update_master_list():
    """更新主列表"""
    print("=" * 60)
    print("🐵 港股代碼更新腳本")
    print("=" * 60)
    
    # 讀取現有列表
    existing = set()
    existing_df = None
    
    if os.path.exists(OUTPUT_FILE):
        print(f"\n📖 讀取現有列表: {OUTPUT_FILE}")
        existing_df = pd.read_csv(OUTPUT_FILE)
        existing = set(existing_df['symbol'].tolist())
        print(f"   已有的股票數量: {len(existing)}")
    
    print(f"\n🔍 開始掃描 HKEX 主板股票...")
    print(f"   範圍: 0001 - 9999")
    print(f"   預計時間: 15-30 分鐘")
    print()
    
    # 掃描範圍 (分段以便追蹤進度)
    ranges = [
        (1, 1000),
        (1001, 2000),
        (2001, 3000),
        (3001, 4000),
        (4001, 5000),
        (5001, 6000),
        (6001, 7000),
        (7001, 8000),
        (8001, 9000),
        (9001, 9999),
    ]
    
    all_results = []
    
    for start, end in ranges:
        print(f"\n📊 掃描 {start:04d} - {end:04d}...")
        results = scan_range(start, end)
        all_results.extend(results)
        print(f"   找到: {len(results)} 支股票")
    
    # 轉為 DataFrame
    df = pd.DataFrame(all_results)
    
    # 去重
    df = df.drop_duplicates(subset=['symbol'])
    df = df.sort_values('symbol')
    
    # 保存
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 60)
    print(f"✅ 更新完成！")
    print(f"   總股票數量: {len(df)}")
    print(f"   保存至: {OUTPUT_FILE}")
    print("=" * 60)
    
    # 顯示前20支
    print("\n📋 前20支股票:")
    print(df[['code', 'name', 'sector']].head(20).to_string(index=False))
    
    return df


def quick_update():
    """快速更新 - 只檢查已知範圍"""
    print("🚀 快速更新模式")
    print("   只檢查 0001-2000 常用範圍")
    
    # 常用代碼範圍 (根據HKEX數據，大部分股票在這範圍)
    common_codes = []
    
    # 001-099: 藍籌大佬
    for i in range(1, 100):
        common_codes.append(str(i).zfill(4))
    
    # 100-999: 主要公司
    for i in range(100, 1000):
        common_codes.append(str(i).zfill(4))
    
    # 1000-1999: 中型公司
    for i in range(1000, 2000):
        common_codes.append(str(i).zfill(4))
    
    # 2000-2999: GEM (創業板) + 部分主板
    # 3000-3999: GEM + 部分主板
    # 6000-6999: 主要主板 (騰訊 0700, 阿里 9988 等)
    for i in range(6000, 7000):
        common_codes.append(str(i).zfill(4))
    
    print(f"   將檢查 {len(common_codes)} 個代碼...")
    
    results = []
    for i, code in enumerate(common_codes):
        if i % 50 == 0:
            print(f"   進度: {i}/{len(common_codes)}")
        
        symbol = f"{code}.HK"
        result = check_stock(symbol)
        if result:
            results.append(result)
        
        time.sleep(DELAY)
    
    df = pd.DataFrame(results)
    df = df.drop_duplicates(subset=['symbol'])
    df = df.sort_values('symbol')
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 完成！找到 {len(df)} 支股票")
    return df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        df = quick_update()
    else:
        df = update_master_list()
