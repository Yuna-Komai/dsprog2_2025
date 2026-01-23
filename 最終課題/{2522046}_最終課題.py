import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import pandas as pd
import logging
import unittest
from typing import Optional, Dict, List, Any

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class SaitamaHousingScraper:
    """Webから住宅データを取得するクラス"""
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_data(self) -> List[tuple]:
        """実際にスクレイピングを行う（ここでは構造の例を示します）"""
        try:
            # 実際には対象のURLにアクセス
            # response = requests.get(self.base_url, headers=self.headers)
            # soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info("Webサイトからデータを取得中...")
            time.sleep(1)  # サーバー負荷軽減のための待機

            # --- ここで解析ロジック（例） ---
            # 取得したHTMLからデータを抽出するシミュレーション
            # 実際は soup.find_all(...) などで抽出します
            scraped_data = [
                ('さいたま市浦和区', 6800, 62.5), ('さいたま市大宮区', 6500, 60.1),
                ('戸田市', 6200, 58.0), ('和光市', 6100, 59.5), ('川口市', 5950, 61.8),
                ('秩父市', 3100, 93.0)
            ]
            return scraped_data

        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return []

class SaitamaHousingAnalyzer:
    """データベース保存と分析を担当するクラス"""
    def __init__(self, db_name: str = 'saitama_housing_final.db'):
        self.db_name = db_name

    def setup_db(self, data: List[tuple]):
        """取得データをDBに格納する"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS housing_stats')
            cursor.execute('''
                CREATE TABLE housing_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_name TEXT NOT NULL,
                    avg_rent REAL,
                    avg_area REAL
                )
            ''')
            cursor.executemany(
                'INSERT INTO housing_stats (city_name, avg_rent, avg_area) VALUES (?, ?, ?)', 
                data
            )
            conn.commit()
            logger.info(f"DBに {len(data)} 件のデータを保存しました。")

    def get_data_by_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        with sqlite3.connect(self.db_name) as conn:
            return pd.read_sql(query, conn, params=params)

    def compare_city_dynamic(self, target_city: str) -> Optional[Dict[str, Any]]:
        df = self.get_data_by_query("SELECT * FROM housing_stats")
        if df.empty: return None
        
        avg_rent = df['avg_rent'].mean()
        city_data = df[df['city_name'].str.contains(target_city)]
        
        if city_data.empty: return None
        
        row = city_data.iloc[0]
        return {
            "city": row['city_name'],
            "rent": row['avg_rent'],
            "diff_from_avg": avg_rent - row['avg_rent']
        }

def main():
    # 1. スクレイピング実行
    # 本来は実際のURLを指定します
    scraper = SaitamaHousingScraper("https://example.com/saitama-housing")
    data = scraper.fetch_data()

    if not data:
        logger.error("データが取得できませんでした。")
        return

    # 2. DB構築と分析
    analyzer = SaitamaHousingAnalyzer()
    analyzer.setup_db(data)
    
    # 3. 結果の表示
    analysis = analyzer.compare_city_dynamic("秩父市")
    if analysis:
        print(f"\n【分析結果】\n{analysis['city']}の家賃は県平均より {analysis['diff_from_avg']:,.0f}円 安いです。")

if __name__ == "__main__":
    main()