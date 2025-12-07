from kivy.app import App
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

import sqlite3, os
from datetime import datetime, timedelta, date

home_dir, ui_month, ui_year, popup_day = None, None, None, None

KV = """
<CustomButton@Button>:
    background_normal: ''
    background_color: (0.9, 0.9, 0.9, 1)
    color: (0, 0, 0, 1)
    font_size: '16sp'
    border: (2, 2, 2, 2)
    
<DayButton@Button>:
    background_normal: ''
    color: (0, 0, 0, 1)
    font_size: '14sp'
    markup: True
    halign: 'center'
    valign: 'middle'
    border: (1, 1, 1, 1)

<HeaderButton@Button>:
    background_normal: ''
    background_color: (0.2, 0.6, 0.8, 1)
    color: (1, 1, 1, 1)
    font_size: '18sp'
    bold: True
    size_hint_y: None
    height: dp(50)

Screen:
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)
        canvas.before:
            Color:
                rgba: 0.95, 0.95, 0.95, 1
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            HeaderButton:
                text: '<'
                size_hint_x: None
                width: dp(50)
                on_press: app.prev_button_clicked()
            Label:
                id: mont_label
                text: 'Месяц'
                font_size: '24sp'
                bold: True
                color: (0.2, 0.2, 0.2, 1)
                size_hint_y: None
                height: dp(50)
            HeaderButton:
                text: '>'
                size_hint_x: None
                width: dp(50)
                on_press: app.next_button_clicked()

        GridLayout:
            id: mont_box
            cols: 7
            spacing: dp(5)
            padding: dp(5)
            size_hint: (1, 1)

<CustomPopup>:
    size_hint: 0.9, 0.9
    auto_dismiss: False
    title_size: '20sp'
    title_align: 'center'
    separator_color: [0.2, 0.6, 0.8, 1]
    separator_height: dp(2)
    
    BoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(15)
        canvas.before:
            Color:
                rgba: 0.95, 0.95, 0.95, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "Заметка на день"
            font_size: '18sp'
            bold: True
            size_hint_y: None
            height: dp(30)
            color: (0.2, 0.2, 0.2, 1)

        TextInput:
            id: first_input
            hint_text: "Введите описание дня"
            foreground_color: 0.1, 0.1, 0.1, 1
            background_color: 1, 1, 1, 1
            cursor_color: 0.2, 0.6, 0.8, 1
            selection_color: 0.2, 0.6, 0.8, 0.5
            multiline: True
            font_size: '16sp'
            size_hint_y: None
            height: dp(150)

        Label:
            text: "Краткий текст для главной страницы"
            font_size: '16sp'
            bold: True
            size_hint_y: None
            height: dp(30)
            color: (0.2, 0.2, 0.2, 1)

        TextInput:
            id: two_input
            hint_text: "Введите краткий текст"
            foreground_color: 0.1, 0.1, 0.1, 1
            background_color: 1, 1, 1, 1
            cursor_color: 0.2, 0.6, 0.8, 1
            selection_color: 0.2, 0.6, 0.8, 0.5
            multiline: True
            font_size: '16sp'
            size_hint_y: None
            height: dp(80)

        Label:
            text: "Выберите цвет дня:"
            font_size: '16sp'
            bold: True
            size_hint_y: None
            height: dp(30)
            color: (0.2, 0.2, 0.2, 1)

        GridLayout:
            id: buttons_container
            cols: 5
            spacing: dp(5)
            padding: dp(5)
            size_hint_y: None
            height: dp(120)

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            padding: dp(5)
            CustomButton:
                text: "Сохранить и закрыть"
                background_color: (0.2, 0.6, 0.8, 1)
                color: (1, 1, 1, 1)
                on_press: root.dismiss()
"""

class CustomPopup(Popup):
    def save_text(self):
        description = self.ids.first_input.text
        letter = self.ids.two_input.text
        day = Database.get_day(ui_month, ui_year, int(popup_day)-1)
        Database.save_day_data(
            year=ui_year,
            month=ui_month,
            day=int(popup_day)-1,
            color=day[0],
            letter=letter,
            description=description
        )
        app = App.get_running_app()
        app.calendar_render(ui_month, ui_year)

    def dismiss(self, *args, **kwargs):
        self.save_text()
        super().dismiss(*args, **kwargs)

class monts:
    months_ru = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    current_month = datetime.now().month
    month_name_ru = months_ru[current_month - 1]

    @staticmethod
    def get_ru_mont_name(number):
        month_name_ru = monts.months_ru[number - 1]
        return month_name_ru

    @staticmethod
    def days_in_month(year: int, month: int):
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        last_day_of_month = datetime(next_year, next_month, 1) - timedelta(microseconds=1)
        return last_day_of_month.day

    @staticmethod
    def get_weekday(year, month, day):
        d = date(year, month, day)
        return d.weekday()

class Database:
    @staticmethod
    def create_database():
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS months (
            month_year TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            order_num INTEGER
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS days (
            month_year TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            color TEXT,
            letter TEXT,
            description TEXT,
            FOREIGN KEY (month_year) REFERENCES months(month_year) ON DELETE CASCADE,
            PRIMARY KEY (month_year, day_number)
        )''')

        conn.commit()
        conn.close()

    @staticmethod
    def month_exists(month, year):
        month_year = f"{month}.{year}"
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM months WHERE month_year = ?', (month_year,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def add_month(month, year, name, order_num=None):
        month_year = f"{month}.{year}"
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO months (month_year, name, order_num)
        VALUES (?, ?, ?)
        ''', (month_year, name, order_num))
        conn.commit()
        conn.close()
        return month_year

    @staticmethod
    def add_day(month, year, day_number, color=None, letter=None, description=None):
        month_year = f"{month}.{year}"
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO days (month_year, day_number, color, letter, description)
        VALUES (?, ?, ?, ?, ?)
        ''', (month_year, day_number, color, letter, description))
        conn.commit()
        conn.close()

    @staticmethod
    def get_month_days(month, year):
        month_year = f"{month}.{year}"
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT day_number, color, letter, description
        FROM days
        WHERE month_year = ?
        ORDER BY day_number
        ''', (month_year,))
        days = cursor.fetchall()
        conn.close()
        return days

    @staticmethod
    def get_all_months():
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT month_year, name, order_num FROM months ORDER BY order_num, month_year')
        months = cursor.fetchall()
        conn.close()
        return months

    @staticmethod
    def get_day(month, year, day_number):
        month_year = f"{month}.{year}"
        if home_dir is None: return
        db_path = os.path.join(home_dir, "calendar.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT color, letter, description
        FROM days
        WHERE month_year = ? AND day_number = ?
        ''', (month_year, day_number))
        day = cursor.fetchone()
        conn.close()
        return day

    @staticmethod
    def save_day_data(year, month, day, color=None, letter=None, description=None):
        if home_dir is None:
            print("Ошибка: home_dir не определен")
            return False

        try:
            month_year = f"{month}.{year}"
            db_path = os.path.join(home_dir, "calendar.db")

            if not os.path.exists(db_path):
                Database.create_database()

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT 1 FROM months WHERE month_year = ?', (month_year,))
            if not cursor.fetchone():
                month_names = [
                    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
                ]
                month_name = month_names[month-1] if 1 <= month <= 12 else f"Месяц {month}"
                cursor.execute(
                    'INSERT INTO months (month_year, name) VALUES (?, ?)',
                    (month_year, month_name)
                )
                conn.commit()

            cursor.execute('''
                INSERT OR REPLACE INTO days
                (month_year, day_number, color, letter, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (month_year, day, color, letter, description))

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            print(f"Ошибка SQLite при сохранении дня: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            print(f"Общая ошибка при сохранении дня: {e}")
            if 'conn' in locals():
                conn.close()
            return False

class MyApp(App):
    def build(self):
        global home_dir
        home_dir = self.user_data_dir
        return Builder.load_string(KV)

    def on_start(self):
        now = datetime.now()
        month, year = now.month, now.year
        Database.create_database()
        self.start_funk(month, year)

    def start_funk(self, month, year):
        global ui_month, ui_year
        if Database.month_exists(month, year) and Database.get_month_days(month, year) != []:
            ui_month, ui_year = month, year
            self.calendar_render(month, year)
        else:
            Database.add_month(month, year, str(monts.get_ru_mont_name(month)))
            days_in_mont = monts.days_in_month(year, month)
            for day in range(days_in_mont):
                Database.add_day(month=month, year=year, day_number=day, color="white", letter=" ", description="Здесь пока что пусто")

            ui_month, ui_year = month, year
            self.calendar_render(month, year)

    def prev_button_clicked(self):
        global ui_month, ui_year
        if ui_month == 1:
            new_month = 12
            new_year = ui_year - 1
        else:
            new_month = ui_month - 1
            new_year = ui_year

        ui_month, ui_year = new_month, new_year
        self.start_funk(ui_month, ui_year)

    def next_button_clicked(self):
        global ui_month, ui_year
        if ui_month == 12:
            new_month = 1
            new_year = ui_year + 1
        else:
            new_month = ui_month + 1
            new_year = ui_year

        ui_month, ui_year = new_month, new_year
        self.start_funk(ui_month, ui_year)

    def calendar_render(self, month, year):
        weekday_num = monts.get_weekday(year, month, 1)
        name_month = monts.get_ru_mont_name(month)
        self.root.ids.mont_label.text = f'{name_month} ({month}.{year})'
        self.root.ids.mont_box.clear_widgets()

        may_days = Database.get_month_days(month, year)
        week_names = ['ПН','ВТ','СР','ЧТ','ПТ','СБ','ВС']
        
        # Добавляем заголовки дней недели с увеличенным шрифтом
        for day_name in week_names:
            btn = Button(
                text=f"[size=24]{day_name}[/size]",
                markup=True,
                bold=True,
                color=(0.2, 0.2, 0.2, 1),
                background_color=(0.8, 0.8, 0.8, 1),
                size_hint=(1, 1),
                background_normal=''
            )
            self.root.ids.mont_box.add_widget(btn)
            
        # Добавляем пустые кнопки для выравнивания
        if int(weekday_num) < 7:
            for x in range(weekday_num):
                btn = Button(
                    text='',
                    background_color=(0.95, 0.95, 0.95, 1),
                    size_hint=(1, 1),
                    background_normal=''
                )
                self.root.ids.mont_box.add_widget(btn)
                
        # Добавляем дни месяца с увеличенными цифрами
        for day in may_days:
            color_name = day[1]
            color_dict = {
                "Красный": (255, 0, 0),
                "Оранжевый": (255, 165, 0),
                "Жёлтый": (255, 255, 0),
                "Зелёный": (0, 255, 0),
                "Бирюзовый": (0, 255, 255),
                "Синий": (0, 0, 255),
                "Фиолетовый": (148, 0, 211),
                "Светло-серый": (200, 200, 200),
                "Тёмно-серый": (50, 50, 50),
                "white": (255, 255, 255)
            }

            rgb = color_dict.get(color_name, (255, 255, 255))
            kivy_color = (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0, 1)

            btn = Button(
                text=f"[size=24][color=000000][b]{int(day[0]) + 1}[/b][/color][/size]\n[size=28]{day[2]}[/size]",
                markup=True,
                halign='center',
                valign='middle',
                color=(0, 0, 0, 1),
                background_color=kivy_color,
                size_hint=(1, 1),
                background_normal=''
            )
            btn.day_number = int(day[0]) + 1
            btn.bind(on_press=self.on_day_button_press)
            self.root.ids.mont_box.add_widget(btn)

    @staticmethod
    def on_button_press(color_rgb, color_name):
        day = Database.get_day(ui_month, ui_year, int(popup_day)-1)
        Database.save_day_data(
            year=ui_year,
            month=ui_month,
            day=int(popup_day)-1,
            color=str(color_name),
            letter=day[1],
            description=day[2]
        )

    def on_day_button_press(self, instance):
        global popup_day
        popup_day = instance.day_number
        popup = CustomPopup()
        popup.title = f'{instance.day_number}.{ui_month}.{ui_year}'
        day = Database.get_day(month=ui_month, year=ui_year, day_number=int(instance.day_number)-1)
        popup.ids.first_input.text = day[2] if day and day[2] else ""
        popup.ids.two_input.text = day[1] if day and day[1] else ""
        
        buttons_container = popup.ids.buttons_container
        buttons_container.clear_widgets()
        
        colors_data = [
            ((255, 0, 0), "Красный"),
            ((255, 165, 0), "Оранжевый"),
            ((255, 255, 0), "Жёлтый"),
            ((0, 255, 0), "Зелёный"),
            ((0, 255, 255), "Бирюзовый"),
            ((0, 0, 255), "Синий"),
            ((148, 0, 211), "Фиолетовый"),
            ((200, 200, 200), "Светло-серый"),
            ((50, 50, 50), "Тёмно-серый"),
            ((255, 255, 255), "Белый")
        ]

        for color_rgb, color_name in colors_data:
            btn = Button(
                text=color_name,
                size_hint_y=None,
                height=dp(40),
                background_normal='',
                background_color=(color_rgb[0]/255.0, color_rgb[1]/255.0, color_rgb[2]/255.0, 1),
                color=(0, 0, 0, 1) if sum(color_rgb) > 382 else (1, 1, 1, 1)
            )
            btn.bind(on_press=lambda instance, c=color_rgb, n=color_name: MyApp.on_button_press(c, n))
            buttons_container.add_widget(btn)
            
        popup.open()

if __name__ == '__main__':
    MyApp().run()
