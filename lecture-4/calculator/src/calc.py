import flet as ft
import math # 科学計算のためにmathモジュールをインポートします

class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text
        # スタイルを調整してボタンの見た目を均一にします
        self.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(10)),
            padding=ft.padding.symmetric(vertical=15, horizontal=0)
        )


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK

# 1. 科学計算モード用の新しいボタンクラス
class ScienceActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        # 科学計算ボタンのexpandはデフォルト1にします
        CalcButton.__init__(self, text, button_clicked, expand=1)
        self.bgcolor = ft.Colors.BLUE_GREY_400 
        self.color = ft.Colors.WHITE


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=40) # サイズを大きくしました
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end"),
                
                # 2. 科学計算ボタンの行を追加
                ft.Row(
                    controls=[
                        ScienceActionButton(text="sin", button_clicked=self.button_clicked),
                        ScienceActionButton(text="cos", button_clicked=self.button_clicked),
                        ScienceActionButton(text="tan", button_clicked=self.button_clicked),
                        ScienceActionButton(text="sqrt", button_clicked=self.button_clicked),
                        ScienceActionButton(text="x^2", button_clicked=self.button_clicked), 
                    ]
                ),

                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    # 3. button_clicked メソッドに科学計算ロジックを追加
    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                self.result.value = data
            else:
                # 既に小数点がある場合は追加しない
                if data == "." and "." in self.result.value:
                    pass
                else:
                    self.result.value = self.result.value + data
            self.new_operand = False

        elif data in ("+", "-", "*", "/"):
            # 演算子が押されたら、一旦それまでの計算を実行
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = 0
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data in ("="):
            self.result.value = self.calculate(self.operand1, float(self.result.value), self.operator)
            self.reset() # 計算後はリセットして次の計算に備える

        elif data in ("%"):
            self.result.value = self.format_number(float(self.result.value) / 100)
            self.reset() # パーセント計算後はリセット

        elif data in ("+/-"):
            current_value = float(self.result.value)
            self.result.value = self.format_number(-current_value)
            self.new_operand = True # 結果が表示されたので、次の数字入力でリセット

        # --- 科学計算ロジック ---
        elif data in ("sin", "cos", "tan", "sqrt", "x^2"):
            try:
                current_value = float(self.result.value)
                
                if data == "sin":
                    # math.sin はラジアンを期待
                    new_value = math.sin(current_value) 
                elif data == "cos":
                    new_value = math.cos(current_value)
                elif data == "tan":
                    new_value = math.tan(current_value)
                elif data == "sqrt":
                    if current_value < 0:
                        self.result.value = "Error"
                        self.reset()
                        self.update()
                        return
                    new_value = math.sqrt(current_value)
                elif data == "x^2":
                    new_value = current_value ** 2

                self.result.value = str(self.format_number(new_value))
                self.new_operand = True
                
            except ValueError:
                self.result.value = "Error"
                self.reset()
        # --- 科学計算ロジックここまで ---

        self.update()

    def format_number(self, num):
        # 結果が整数なら整数として表示し、それ以外はそのまま返す
        if abs(num - round(num)) < 1e-9: # 浮動小数点の誤差を考慮
            return int(round(num))
        else:
            return num

    def calculate(self, operand1, operand2, operator):

        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)
        
        # 演算子が押されていない場合は、現在の値を返す
        return self.format_number(operand2)


    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # ページ設定でボタンを見やすくする
    page.fonts = {
        "RobotoMono": "fonts/RobotoMono-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="RobotoMono")
    
    calc = CalculatorApp()
    page.add(calc)


ft.app(main)