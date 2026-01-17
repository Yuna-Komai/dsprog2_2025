import flet as ft
import requests
import datetime
import sqlite3
import os

# --- 設定・定数 ---
# 課題要件に基づき SQLite DB名を指定
DB_NAME = "weather_history.db"
AREA_API_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_API_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"

# --- データベース関連の関数 (DB格納・設計の要件) ---

def init_db():
    """DBの初期化: テーブル設計とプライマリーキーの設定"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 課題のヒントに基づき、area_codeとdateをキーとして一意性を確保
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_code TEXT,
            area_name TEXT,
            date TEXT,
            weather TEXT,
            temp_max TEXT,
            temp_min TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(area_code, date)
        )
    ''')
    conn.commit()
    conn.close()

def save_forecast_to_db(area_code, area_name, date_str, weather, t_max, t_min):
    """取得したJSONデータをDBに移行する処理"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 重複がある場合は最新の天気情報で更新（正規化とデータ整合性の考慮）
        cursor.execute('''
            INSERT OR REPLACE INTO weather_forecasts (area_code, area_name, date, weather, temp_max, temp_min)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (area_code, area_name, date_str, weather, t_max, t_min))
        conn.commit()
    except sqlite3.Error as e:
        print(f"DB保存エラー: {e}")
    finally:
        conn.close()

def get_forecast_from_db(area_code, date_str):
    """日付選択で過去の予報を閲覧するための関数"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT weather, temp_max, temp_min FROM weather_forecasts 
        WHERE area_code = ? AND date = ?
    ''', (area_code, date_str))
    result = cursor.fetchone()
    conn.close()
    return result

# --- UIヘルパー関数 ---

def get_weather_icon(weather_str):
    if "晴" in weather_str and "曇" not in weather_str and "雨" not in weather_str:
        return ft.Icons.WB_SUNNY, "orange"
    elif "雪" in weather_str:
        return ft.Icons.AC_UNIT, "lightBlue"
    elif "雨" in weather_str:
        return ft.Icons.UMBRELLA, "blue"
    elif "曇" in weather_str:
        return ft.Icons.CLOUD, "grey"
    else:
        return ft.Icons.QUESTION_MARK, "black"

def create_forecast_card(date_str, weather_str, temp_min_str=None, temp_max_str=None):
    icon, icon_color = get_weather_icon(weather_str)
    
    temp_row = ft.Row([
        ft.Text(f"{temp_min_str if temp_min_str else '--'}℃", color="blue"),
        ft.Text("/"),
        ft.Text(f"{temp_max_str if temp_max_str else '--'}℃", color="red")
    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER)

    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text(date_str, size=14, weight="bold"),
                ft.Text(weather_str.split("　")[0], size=12, text_align="center"),
                ft.Icon(icon, size=36, color=icon_color),
                temp_row,
            ], alignment="center", horizontal_alignment="center", spacing=5),
            padding=10, width=130, height=160
        )
    )

# --- メインロジック ---

all_areas = {}

def main(page: ft.Page):
    init_db() # 起動時にDBテーブル作成
    
    page.title = "天気予報アプリ (DB/Git Flow課題対応版)"
    page.window_width = 1000
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.LIGHT

    # 現在選択されている地域情報を保持
    state = {"area_code": "130000", "area_name": "東京都"}

    # UIコンポーネント
    forecast_display = ft.Row(wrap=True, spacing=15)
    history_display = ft.Container()
    
    # 過去予報閲覧機能（オプション要件）のためのDatePicker
    def on_date_picked(e):
        if date_picker.value:
            selected_date = date_picker.value.strftime("%Y-%m-%d")
            db_data = get_forecast_from_db(state["area_code"], selected_date)
            
            if db_data:
                weather, t_max, t_min = db_data
                history_display.content = ft.Column([
                    ft.Text(f"📅 DBに保存されている予報 ({selected_date})", size=16, weight="bold"),
                    create_forecast_card(selected_date, weather, t_min, t_max)
                ])
            else:
                history_display.content = ft.Text(f"❌ {selected_date} のデータはDBに見当たりません。", color="orange")
            page.update()

    date_picker = ft.DatePicker(on_change=on_date_picked)
    page.overlay.append(date_picker)

    def fetch_weather(region_code, region_name):
        state["area_code"] = region_code
        state["area_name"] = region_name
        
        forecast_display.controls = [ft.ProgressRing()]
        history_display.content = None
        page.update()

        try:
            parent_office = region_code
            for office_code, office_info in all_areas.get("offices", {}).items():
                if region_code in office_info.get("children", []):
                    parent_office = office_code
                    break
            
            res = requests.get(f"{FORECAST_API_BASE_URL}{parent_office}.json")
            data = res.json()
            
            time_defines = data[0]['timeSeries'][0]['timeDefines']
            weather_data = next((a for a in data[0]['timeSeries'][0]['areas'] if a['area']['code'] == region_code), data[0]['timeSeries'][0]['areas'][0])
            
            temp_data = None
            if len(data) > 1:
                for ts in data[1]['timeSeries']:
                    for area in ts['areas']:
                        if area['area']['code'] == region_code:
                            temp_data = area
                            break

            cards = []
            for i in range(len(time_defines)):
                d_str = datetime.datetime.fromisoformat(time_defines[i]).strftime("%Y-%m-%d")
                w_str = weather_data['weathers'][i] if i < len(weather_data['weathers']) else "情報なし"
                t_min = temp_data['tempsMin'][i] if temp_data and 'tempsMin' in temp_data and i < len(temp_data['tempsMin']) else None
                t_max = temp_data['tempsMax'][i] if temp_data and 'tempsMax' in temp_data and i < len(temp_data['tempsMax']) else None
                
                # 表示の際にDBへ移行（課題の「JSONからDBに移行」要件）
                save_forecast_to_db(region_code, region_name, d_str, w_str, t_max, t_min)
                cards.append(create_forecast_card(d_str, w_str, t_min, t_max))
            
            forecast_display.controls = cards
            page.update()

        except Exception as e:
            forecast_display.controls = [ft.Text(f"エラー: {e}", color="red")]
            page.update()

    # 地域リストの生成
    region_list = ft.Column(scroll="adaptive", expand=True)

    def build_sidebar():
        global all_areas
        res = requests.get(AREA_API_URL)
        all_areas = res.json()
        
        controls = [ft.Text("地域選択", size=20, weight="bold"), ft.Divider()]
        for c_code, c_info in all_areas["centers"].items():
            office_tiles = []
            for o_code in c_info.get("children", []):
                if o_code in all_areas["offices"]:
                    office_name = all_areas["offices"][o_code]["name"]
                    class_tiles = []
                    for cl_code in all_areas["offices"][o_code].get("children", []):
                        if cl_code in all_areas["class10s"]:
                            cl_name = all_areas["class10s"][cl_code]["name"]
                            class_tiles.append(ft.ListTile(
                                title=ft.Text(cl_name),
                                on_click=lambda e, code=cl_code, name=cl_name: fetch_weather(code, name),
                                dense=True
                            ))
                    office_tiles.append(ft.ExpansionTile(title=ft.Text(office_name), controls=class_tiles))
            controls.append(ft.ExpansionTile(title=ft.Text(c_info["name"]), controls=office_tiles))
        
        region_list.controls = controls
        page.update()

    # --- レイアウト（エラー修正箇所） ---
    # Columnからpadding引数を削除し、Containerでラップしています
    main_content_inner = ft.Column([
        ft.Row([
            ft.Text(f"天気予報表示", size=24, weight="bold"),
            ft.ElevatedButton("過去予報をDB検索", icon=ft.Icons.SEARCH_ROUNDED, on_click=lambda _: date_picker.pick_date())
        ], alignment="spaceBetween"),
        forecast_display,
        ft.Divider(),
        history_display
    ], expand=True, scroll="adaptive")

    main_content = ft.Container(content=main_content_inner, padding=20, expand=True)

    page.add(ft.Row([
        ft.Container(region_list, width=250, bgcolor="#f5f5f5", padding=10),
        ft.VerticalDivider(width=1),
        main_content
    ], expand=True))

    build_sidebar()
    fetch_weather("130000", "東京都") # 初期表示は東京

ft.app(target=main)