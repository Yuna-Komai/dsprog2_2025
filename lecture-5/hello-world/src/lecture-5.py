import flet as ft
import requests
import datetime
import json

# --- 気象庁 API エンドポイント ---
AREA_API_URL = "http://www.jma.go.jp/bosai/common/const/area.json" # 地域リスト取得用API
FORECAST_API_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/" # 天気予報取得用API

# --- ヘルパー関数 ---

def get_weather_icon(weather_str):
    """天気文字列に基づいて適切なFletアイコンと色を返す関数"""
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
    """天気予報の日ごとのカードを作成する関数"""
    icon, icon_color = get_weather_icon(weather_str)
    
    temp_text_ui = ft.Text("")
    if temp_min_str is not None and temp_max_str is not None:
        temp_max_ui = ft.Text(f"{temp_max_str}℃", size=14, weight=ft.FontWeight.BOLD, color="red")
        temp_min_ui = ft.Text(f"{temp_min_str}℃", size=14, weight=ft.FontWeight.BOLD, color="blue")
        temp_text_ui = ft.Row([temp_min_ui, ft.Text("/", size=14), temp_max_ui], spacing=5)

    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(date_str, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(weather_str.split("　")[0], size=12),
                    ft.Icon(icon, size=36, color=icon_color),
                    temp_text_ui,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=10,
            width=130,
            height=180,
            alignment=ft.alignment.center,
        ),
        elevation=2
    )

def fetch_weather_forecast(region_code, region_name, forecast_view, page):
    """選択された地域の天気予報を取得・表示する関数"""
    
    # 親のofficeコードを見つける
    parent_office = region_code
    for office_code, office_info in all_areas["offices"].items():
        if region_code in office_info.get("children", []):
            parent_office = office_code
            break
    
    forecast_url = f"{FORECAST_API_BASE_URL}{parent_office}.json"
    
    # ロード中表示
    forecast_view.content = ft.Row(
        [ft.ProgressRing(), ft.Text(f"『{region_name}』の天気予報を取得中...", size=16)],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    page.update()
    
    try:
        response = requests.get(forecast_url)
        response.raise_for_status()
        data = response.json()
        
        time_defines = data[0]['timeSeries'][0]['timeDefines']
        
        # 該当エリアのデータを取得
        weather_data = None
        for area in data[0]['timeSeries'][0]['areas']:
            if area['area']['code'] == region_code:
                weather_data = area
                break
        
        if not weather_data:
            # 主要都市のデータを使用
            weather_data = data[0]['timeSeries'][0]['areas'][0]
        
        # 気温データの取得
        temp_data = None
        if len(data) > 1 and len(data[1]['timeSeries']) > 1:
            for area in data[1]['timeSeries'][1]['areas']:
                if area['area']['code'] == region_code:
                    temp_data = area
                    break
            
            if not temp_data:
                # 該当エリアがない場合は主要都市のデータを使用
                temp_data = data[1]['timeSeries'][1]['areas'][0]

        forecast_cards = []
        
        for i in range(len(time_defines)):
            date_obj = datetime.datetime.fromisoformat(time_defines[i])
            date_str = date_obj.strftime("%Y-%m-%d")
            
            weather_str = weather_data['weathers'][i] if i < len(weather_data['weathers']) else "情報なし"
            
            temp_min_str = None
            temp_max_str = None
            if temp_data and 'tempsMin' in temp_data and i < len(temp_data['tempsMin']):
                temp_min_str = temp_data['tempsMin'][i]
            if temp_data and 'tempsMax' in temp_data and i < len(temp_data['tempsMax']):
                temp_max_str = temp_data['tempsMax'][i]
            
            forecast_cards.append(create_forecast_card(date_str, weather_str, temp_min_str, temp_max_str))

        forecast_view.content = ft.Column(
            [
                ft.Text(f"⚡️ {region_name}の天気予報", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    forecast_cards,
                    wrap=True,
                    spacing=15,
                    alignment=ft.MainAxisAlignment.START,
                    scroll=ft.ScrollMode.ADAPTIVE
                )
            ],
            expand=True
        )
        page.update()

    except requests.exceptions.RequestException as e:
        forecast_view.content = ft.Text(f"天気予報の取得に失敗しました (API通信エラー): {e}", color="red")
        page.update()
    except Exception as e:
        forecast_view.content = ft.Column([
            ft.Text(f"予報データの解析中にエラーが発生しました: {type(e).__name__}: {e}", color="red"),
            ft.Text(f"詳細: {forecast_url}", size=12, color="grey")
        ])
        page.update()

# --- メイン関数 ---
all_areas = {}  # グローバル変数として定義

def main(page: ft.Page):
    global all_areas
    
    # 初期設定
    page.title = "天気予報アプリ"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_height = 650
    page.window_width = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # --- イベントハンドラ ---
    def handle_region_click(e):
        """地域がクリックされたときの処理"""
        selected_region_code = e.control.data 
        if isinstance(e.control.title, ft.Text):
            region_name = e.control.title.value
        else:
            region_name = "選択地域"
        
        fetch_weather_forecast(selected_region_code, region_name, forecast_view, page)

    # --- UI要素の定義 ---

    # 天気予報を表示するコンテナ
    forecast_view = ft.Container(
        content=ft.Text("左側の地域リストから、予報を見たい地域を選択してください。", size=16, color="grey"),
        expand=True,
        padding=ft.padding.all(20)
    )

    # 地域リストのプレースホルダー (ロード中の表示)
    region_list_content = ft.Column(
        [
            ft.Text("地域を選択", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            ft.Row([ft.ProgressRing(width=20, height=20), ft.Text("地域データを取得中...")], spacing=10, alignment=ft.MainAxisAlignment.START),
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
        spacing=0,
        expand=True
    )
    
    region_list_column_container = ft.Container(
        content=region_list_content,
        width=300,
        padding=10,
        bgcolor="#f0f0f0",
        border_radius=ft.border_radius.all(5),
        expand=False
    )
    
    # メインレイアウトをまず追加
    main_layout = ft.Row(
        [
            region_list_column_container,
            forecast_view,
        ],
        expand=True,
        spacing=15
    )
    page.add(main_layout)
    page.update()
    
    
    # --- 地域リストの生成ロジック ---
    def create_region_list(centers, offices, class10s):
        """地域APIデータから階層的なリストビューを生成する"""
        
        region_controls = [
            ft.Text("地域を選択", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10)
        ]

        # 地方のExpansionTileを作成
        for center_code, center_info in centers.items():
            child_tiles = []
            
            # 各地方に含まれる予報区を追加
            for child_code in center_info.get("children", []):
                if child_code in offices:
                    office_name = offices[child_code]["name"]
                    
                    # 府県予報区を都道府県ごとに分類
                    pref_tiles = []
                    for class10_code in offices[child_code].get("children", []):
                        if class10_code in class10s:
                            class10_name = class10s[class10_code]["name"]
                            
                            tile = ft.ListTile(
                                title=ft.Text(class10_name),
                                leading=ft.Icon(ft.Icons.LOCATION_ON),
                                on_click=handle_region_click,
                                data=class10_code
                            )
                            pref_tiles.append(tile)
                    
                    # 府県予報区をExpansionTileとして追加
                    if pref_tiles:
                        child_tiles.append(
                            ft.ExpansionTile(
                                title=ft.Text(office_name),
                                leading=ft.Icon(ft.Icons.MAP),
                                controls=pref_tiles
                            )
                        )
            
            # 地方のExpansionTileを追加 (expanded引数を削除)
            if child_tiles:
                expansion_tile = ft.ExpansionTile(
                    title=ft.Text(center_info["name"], weight=ft.FontWeight.BOLD),
                    leading=ft.Icon(ft.Icons.TERRAIN),
                    controls=child_tiles
                )
                region_controls.append(expansion_tile)
        
        return ft.Column(
            region_controls,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=0,
            expand=True
        )


    # --- データロード関数 ---
    def load_area_data():
        """気象庁APIから地域データを取得し、UIを構築する関数"""
        global all_areas
        
        try:
            # APIから地域リストを取得
            response = requests.get(AREA_API_URL)
            response.raise_for_status()
            all_areas = response.json()
            
            # 地域リストのUIを生成
            centers = all_areas.get("centers", {})
            offices = all_areas.get("offices", {})
            class10s = all_areas.get("class10s", {})
            
            new_region_list = create_region_list(centers, offices, class10s)

            # 既存のプレースホルダーを新しい地域リストで置き換えて画面を更新
            region_list_column_container.content = new_region_list
            
            # デフォルト地域として東京を表示
            fetch_weather_forecast("130000", "東京", forecast_view, page)
            
            page.update()

        except requests.exceptions.RequestException as e:
            region_list_column_container.content = ft.Text(f"地域データの取得に失敗しました (API通信エラー): {e}", color="red")
            page.update()
        except Exception as e:
            region_list_column_container.content = ft.Text(f"予期せぬエラーが発生しました: {type(e).__name__}: {e}", color="red")
            page.update()

    # アプリ起動時に地域データをロード
    load_area_data()

ft.app(target=main)