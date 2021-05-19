import sqlite3
import webbrowser
import time
import datetime
from threading import Thread

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.config import Config

Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
Config.set('graphics', 'width', 400)
Config.set('graphics', 'height', 512)
Config.set('graphics', 'resizable', False)
Config.write()

Builder.load_string('''
<MainPage>:
    name: 'MainPage'
    input_field_new_url: input_field_new_url
    input_field_new_timer: input_field_new_timer
    top_menu_status_label: top_menu_status_label
    main_page_scroll: main_page_scroll
    main_page_scroll_grid:main_page_scroll_grid
    root_grid: root_grid
    
    GridLayout:
        id: root_grid
        cols: 1
    
        GridLayout:
            id: main_page
            cols: 1
            padding: 5
            spacing: 7
            
            AnchorLayout:
                id: main_page_top_menu
                anchor_x: 'center'
                anchor_y: 'top'
                size_hint_y: 0.17
                
                GridLayout:
                    cols: 2
                    spacing: 2
                    
                    TextInput:
                        id: input_field_new_url
                        hint_text: 'Ссылка сайта'
                        multiline: False
                        
                    TextInput:
                        id: input_field_new_timer
                        hint_text: 'Время (мин)'
                        multiline: False
                        size_hint_x: 0.4
                        input_filter: 'int'
                        
                    Label:
                        id: top_menu_status_label
                        text: ''
                        
                    Button:
                        id: top_menu_button_submit
                        size_hint_x: 0.4
                        text: 'Записать'
                        on_press: root.append_new_site()
                        
            ScrollView:
                id: main_page_scroll
                
                GridLayout:
                    id: main_page_scroll_grid
                    cols: 4
                    spacing: 7
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: 40
            
            AnchorLayout:
                id: main_page_bot_menu
                anchor_x: 'center'
                anchor_y: 'bottom'
                size_hint_y: 0.05
                
                Label:
                    text: 'AV_v1.1'
                    
<EditPage>:
    name: 'EditPage'
    root_grid: root_grid
    main_page: main_page
    input_field_edit_url: input_field_edit_url
    input_field_edit_timer: input_field_edit_timer
    input_field_edit_note: input_field_edit_note
    edit_status_label: edit_status_label
    
    GridLayout:
        id: root_grid
        cols: 1
        
        GridLayout:
            id: main_page
            spacing: 7
            cols: 1
            padding: 5
            spacing: 7
            
            GridLayout:
                cols: 2
                size_hint_y: 0.2
                spacing: 3
                
                Label:
                    text: 'Ссылка сайта'
                
                TextInput:
                    id: input_field_edit_url
                
                Label:
                    text: 'Таймер в минутах'
                    
                TextInput:
                    id: input_field_edit_timer
                    input_filter: 'int'
                    
            GridLayout:
                cols: 1
                
                Label:
                    id: edit_status_label
                    text: 'Заметки'
                    size_hint_y: 0.15
                    
                TextInput:
                    id: input_field_edit_note
                    
            GridLayout:
                cols: 2
                size_hint_y: 0.15
                spacing: 5
                
                Button:
                    id: button_edit_save
                    text: 'Сохранить'
                    on_press: root.edit_save()
                    
                Button:
                    id: button_edit_exit
                    text: 'Закрыть'
                    on_press: root.switch_page_main()
''')


def read_config():
    config_file = open('config.txt', 'r')
    path_browser = []
    for config in config_file.readlines():
        path_browser = config
    return (webbrowser.register('Chrome', None,
                                webbrowser.BackgroundBrowser(str(path_browser))))


class Rotation:
    def __init__(self, id_site, url, timer, target_time, note, btn_note, btn_start, btn_del, btn_edit, status):
        self.id_site = id_site
        self.url = url
        self.timer = timer
        self.target_time = target_time
        self.note = note
        self.btn_note = btn_note
        self.btn_start = btn_start
        self.btn_del = btn_del
        self.btn_edit = btn_edit
        self.status = status


class CommandSQL:
    def __init__(self):
        self.data = []
        self.conn = sqlite3.connect('AV.db')
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS sites(
        site_id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        timer FLOAT NOT NULL,
        target_time FLOAT,
        note TEXT)
        ''')
        self.conn.commit()

    def insert_new_data(self, url, timer):
        self.data = [(url, int(timer) * 60, 0, '')]
        self.cur.executemany('INSERT INTO sites VALUES(null, ?, ?, ?, ?)', self.data)
        self.conn.commit()

    def insert_target_time(self, target_time, id_site):
        self.cur.execute('UPDATE sites SET target_time=? WHERE site_id=?', (target_time, id_site))
        self.conn.commit()

    def insert_edit_url_timer_note(self, id_site, new_url, new_timer, new_note):
        self.cur.execute('UPDATE sites SET url=?, timer=?, note=? WHERE site_id=?',
                         (str(new_url), float(new_timer) * 60, str(new_note), int(id_site)))
        self.conn.commit()

    def delete_data(self, dict_id_url):
        for id_site, url in dict_id_url.items():
            self.cur.execute('DELETE FROM sites WHERE site_id=?', [(str(id_site))])
        self.conn.commit()

    def select_all(self):
        self.cur.execute('SELECT * FROM sites ORDER BY timer DESC')
        rows = self.cur.fetchall()
        return rows

    def select_url_timer(self, dict_id_url):
        for key, values in dict_id_url.items():
            self.cur.execute('SELECT url, timer FROM sites WHERE site_id=?', [(str(key))])
        text_url_timer = self.cur.fetchall()
        return text_url_timer

    def select_note(self, dict_id_url):
        for key, values in dict_id_url.items():
            self.cur.execute('SELECT note FROM sites WHERE site_id=?', [(str(key))])
        text_note = self.cur.fetchall()
        return text_note


class MainPage(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        read_config()
        self.output_widgets()

    def change_top_menu_status_label(self):
        time.sleep(5)
        self.top_menu_status_label.text = ''

    def thread_output_widgets(self):
        t1_output_widgets = Thread(target=self.output_widgets())
        t1_output_widgets.start()

    def thread_following_a_link(self, instance):
        t1_following_a_link = Thread(target=self.following_a_link(instance))
        t1_following_a_link.start()

    def append_new_site(self):
        date = datetime.datetime.today().strftime('[%d-%m-%Y    %H:%M]: ')
        if self.input_field_new_url.text != '' and self.input_field_new_timer.text:
            try:
                command_sql.insert_new_data(self.input_field_new_url.text, self.input_field_new_timer.text)
                self.top_menu_status_label.text = 'Запись добавлена.'
                self.input_field_new_url.text = ''
                self.input_field_new_timer.text = ''
            except ArithmeticError as err:
                file_log = open('error.log', 'a')
                log_info = date + str(err)
                file_log.write(log_info + '\n')
                file_log.close()
                self.top_menu_status_label.text = 'Ошибка!'
        else:
            self.top_menu_status_label.text = 'Заполни поля "URL" и "Время (мин)."'
        self.thread_output_widgets()
        t1_top_menu_status_label = Thread(target=self.change_top_menu_status_label)
        t1_top_menu_status_label.start()

    def delete_widget(self, instance):
        command_sql.delete_data(instance.ids)
        self.thread_output_widgets()

    def edit_button(self, instance):
        self.ids.root_grid.clear_widgets()
        self.ids.root_grid.add_widget(EditPage(instance))

    def following_a_link(self, instance):
        real_time = time.time()
        list_url_time = command_sql.select_url_timer(instance.ids)
        url = None
        target_time = None
        id_site = None

        for id_site in instance.ids.keys():
            for url, timer in list_url_time:
                target_time = timer + real_time
        webbrowser.get(using='Chrome').open_new_tab(url)
        command_sql.insert_target_time(target_time, id_site)
        self.thread_output_widgets()

    def create_obj_rotations(self):
        list_objects = []
        rows_db = command_sql.select_all()

        for data in rows_db:
            id_site = data[0]
            url = data[1]
            timer = data[2]
            target_time = data[3]
            note = data[4]
            btn_del = Button(text='DEL', size_hint_x=.25, ids={id_site: url}, on_press=self.delete_widget)
            btn_note = Button(text='Note', disabled=True, ids={id_site: url}, size_hint_x=.2)
            btn_edit = Button(text='Edit', size_hint_x=.25, ids={id_site: url}, on_press=self.edit_button)

            if time.time() < target_time:
                status = 'Disable'
                btn_start = Button(text=url[:20], disabled=True, ids={id_site: url})
            else:
                status = 'Active'
                btn_start = Button(text=url[:20], ids={id_site: url}, on_press=self.thread_following_a_link)

            list_objects.append(
                Rotation(id_site, url, timer, target_time, note, btn_note, btn_start, btn_del, btn_edit, status))
        return list_objects

    def output_widgets(self):
        self.ids.main_page_scroll_grid.clear_widgets()
        list_rotation_objects = self.create_obj_rotations()

        for obj in list_rotation_objects:
            if obj.status == 'Active':
                self.main_page_scroll_grid.add_widget(obj.btn_del)
                self.main_page_scroll_grid.add_widget(obj.btn_start)
                self.main_page_scroll_grid.add_widget(Label(text=str(int(obj.timer) / 60)[:7], size_hint_x=0.2))
                self.main_page_scroll_grid.add_widget(obj.btn_edit)

        for obj in list_rotation_objects:
            if obj.status == 'Disable':
                self.main_page_scroll_grid.add_widget(obj.btn_del)
                self.main_page_scroll_grid.add_widget(obj.btn_start)
                self.main_page_scroll_grid.add_widget(Label(text=str(int(obj.timer) / 60)[:7], size_hint_x=0.2))
                self.main_page_scroll_grid.add_widget(obj.btn_edit)


class EditPage(Screen):
    def __init__(self, instance, **kw):
        super().__init__(**kw)
        list_url_time = command_sql.select_url_timer(instance.ids)
        text_note = command_sql.select_note(instance.ids)

        for id_site in instance.ids.keys():
            for url, timer in list_url_time:
                self.id_site = id_site
                self.url = url
                self.timer = timer / 60

        for text, in text_note:
            self.ids.input_field_edit_note.text = str(text)

        self.ids.input_field_edit_url.text = str(self.url)
        self.ids.input_field_edit_timer.text = str(self.timer)

    def edit_save(self):
        date = datetime.datetime.today().strftime('[%d-%m-%Y    %H:%M]: ')

        try:
            command_sql.insert_edit_url_timer_note(self.id_site, self.ids.input_field_edit_url.text,
                                                   self.ids.input_field_edit_timer.text, self.ids.input_field_edit_note.text)
            self.ids.edit_status_label.text = 'Сохранение успешно!'
        except ArithmeticError as err:
            file_log = open('error.log', 'a')
            log_info = date + str(err)
            file_log.write(log_info + '\n')
            file_log.close()
            self.ids.edit_status_label.text = 'Ошибка!'

    def switch_page_main(self):
        self.ids.root_grid.clear_widgets()
        return self.ids.root_grid.add_widget(MainPage())


class AV_ProgramApp(App):
    def build(self):
        sm.add_widget(MainPage())
        return sm


if __name__ == '__main__':
    command_sql = CommandSQL()
    sm = ScreenManager()
    AV_ProgramApp().run()
