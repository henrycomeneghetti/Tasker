import flet as ft
import sqlite3
import asyncio

class ToDo:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.bgcolor = "#121212"
        self.page.window.resizable = False
        self.page.window.always_on_top = True
        self.page.title = "Tasker"
  


        self.page.window.width = 580
        self.page.window.height = 850
       

        self.task = ''
        self.priority = ''
        self.view = 'all'
        self.selected_priority = "Todas as prioridades"
        self.edit_mode = {}
        self.db_execute('CREATE TABLE IF NOT EXISTS tasks(name, status, priority)')
        self.results = self.db_execute('SELECT * FROM tasks')

        self.offline_tasks = []

        asyncio.run(self.intro_screen())

    def db_execute(self, query, params=[]):
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute(query, params)
            con.commit()
            return cur.fetchall()

    def is_connected(self):
        return True

    async def intro_screen(self):
        welcome_image = ft.Image(src=r'C:\Users\hmq48\OneDrive\Área de Trabalho\TCC\logo.png', width=300, height=200)

        intro_container = ft.Container(
            bgcolor="#121212",
            padding=20,
            content=ft.Column(
                controls=[
                    welcome_image,
                    ft.Text("Bem-vindo ao Tasker!", color="white", size=30),
                    ft.Text("Gerencie suas tarefas de forma eficiente.", color="white", size=20),
                    ft.ElevatedButton("Entrar", on_click=self.show_main_page),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            height=self.page.height
        )

        self.page.add(intro_container)
        self.page.update()

    def show_main_page(self, e):
        self.page.controls.clear()
        self.main_page()
        self.page.update()

    def checked(self, e):
        is_checked = e.control.value
        label = e.control.data

        if self.is_connected():
            if is_checked:
                self.db_execute('UPDATE tasks SET status = "complete" WHERE name = ?', params=[label])
            else:
                self.db_execute('UPDATE tasks SET status = "incomplete" WHERE name = ?', params=[label])
        else:
            for task in self.offline_tasks:
                if task[0] == label:
                    task[1] = "complete" if is_checked else "incomplete"
                    break

        self.update_view()

    def delete_task(self, task_name):
        def confirm_delete(e):
            if self.is_connected():
                self.db_execute('DELETE FROM tasks WHERE name = ?', params=[task_name])
            else:
                self.offline_tasks.append((task_name, "deleted", None))
            self.results = self.db_execute('SELECT * FROM tasks')
            self.update_task_list()
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmação", color="white"),
            content=ft.Text(f"Tem certeza que deseja excluir a tarefa '{task_name}'?", color="white"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Confirmar", on_click=confirm_delete),
            ]
        )
        self.page.dialog = dialog
        self.page.dialog.open = True
        self.page.update()

    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()

    def get_priority_color(self, priority):
        if priority == "Baixa":
            return "blue", "Prioridade baixa"
        elif priority == "Média":
            return "yellow", "Prioridade média"
        elif priority == "Alta":
            return "red", "Prioridade alta"
        return "gray", "Sem prioridade"

    def toggle_edit_mode(self, task_name):
        self.edit_mode[task_name] = not self.edit_mode.get(task_name, False)
        self.update_task_list()

    def save_task_edit(self, e, old_task):
        new_task = e.control.value
        if new_task and new_task != old_task:
            if self.is_connected():
                self.db_execute('UPDATE tasks SET name = ? WHERE name = ?', params=[new_task, old_task])
            else:
                for task in self.offline_tasks:
                    if task[0] == old_task:
                        task[0] = new_task
                        break

        self.edit_mode[old_task] = False
        self.results = self.db_execute('SELECT * FROM tasks')
        self.update_task_list()

    def tasks_container(self):
        tasks_controls = []
        for res in self.results:
            if res:
                task_name, status, priority = res
                color, tooltip_text = self.get_priority_color(priority)
                priority_icon = ft.Container(
                    content=ft.CircleAvatar(
                        bgcolor=color,
                        radius=8,
                    ),
                    tooltip=tooltip_text,
                    padding=5
                )

                row_controls = [
                    ft.Checkbox(
                        label=None,
                        value=True if status == 'complete' else False,
                        on_change=self.checked,
                        data=task_name
                    ),
                    ft.TextField(
                        value=task_name,
                        on_blur=lambda e, old_name=task_name: self.save_task_edit(e, old_name),
                        width=300,
                        autofocus=self.edit_mode.get(task_name, False),
                        read_only=not self.edit_mode.get(task_name, False),
                    ) if self.edit_mode.get(task_name, False) else ft.Text(
                        value=task_name,
                        width=300,
                    ),
                    priority_icon,
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                on_click=lambda e, task_name=task_name: self.toggle_edit_mode(task_name),
                                tooltip="Editar tarefa",
                                icon_color="yellow"
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, name=task_name: self.delete_task(name),
                                icon_color="red",
                                tooltip="Excluir tarefa"
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ]

                tasks_controls.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        return ft.Container(
            height=self.page.height * 0.7,
            content=ft.ListView(
                expand=True,
                spacing=5,
                auto_scroll=True,
                controls=tasks_controls
            )
        )

    def set_value(self, e):
        self.task = e.control.value

    def set_priority(self, e):
        self.priority = e.control.value

    def filter_priority(self, e):
        self.selected_priority = e.control.value
        self.update_view()

    def add(self, e, input_task, input_priority):
        name = self.task
        status = 'incomplete'
        priority = self.priority

        if name and priority != "Selecione a prioridade":
            if self.is_connected():
                self.db_execute('INSERT INTO tasks (name, status, priority) VALUES (?, ?, ?)', params=[name, status, priority])
            else:
                self.offline_tasks.append((name, status, priority))

            input_task.value = ""
            input_priority.value = "Selecione a prioridade"
            self.task = ''
            self.priority = ''

            self.results = self.db_execute('SELECT * FROM tasks')
            self.update_task_list()
        else:
            self.page.add(ft.Text("Por favor, preencha todos os campos corretamente.", color="red"))
            self.page.update()

    def update_task_list(self):
        tasks = self.tasks_container()
        self.page.controls.pop()
        self.page.add(tasks)
        self.page.update()

    def tabs_changed(self, e):
        if e.control.selected_index == 0:
            self.results = self.db_execute('SELECT * FROM tasks')
            self.view = 'all'
        elif e.control.selected_index == 1:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = "incomplete"')
            self.view = 'incomplete'
        elif e.control.selected_index == 2:
            self.results = self.db_execute('SELECT * FROM tasks WHERE status = "complete"')
            self.view = 'complete'

        self.update_view()

    def update_view(self):
        if self.view == 'all':
            query = 'SELECT * FROM tasks'
        elif self.view == 'incomplete':
            query = 'SELECT * FROM tasks WHERE status = "incomplete"'
        elif self.view == 'complete':
            query = 'SELECT * FROM tasks WHERE status = "complete"'

        if self.selected_priority and self.selected_priority != "Todas as prioridades":
            if 'WHERE' in query:
                query += ' AND priority = ?'
            else:
                query += ' WHERE priority = ?'
            self.results = self.db_execute(query, params=[self.selected_priority])
        else:
            self.results = self.db_execute(query)

        self.update_task_list()

    def main_page(self):
        input_task = ft.TextField(
            hint_text="Digite sua tarefa",
            bgcolor='white',
            color='black',
            on_change=self.set_value,
            expand=True
        )

        input_priority = ft.Dropdown(
            hint_text="Selecione a prioridade",
            options=[
                ft.dropdown.Option("Selecione a prioridade"),
                ft.dropdown.Option("Baixa"),
                ft.dropdown.Option("Média"),
                ft.dropdown.Option("Alta"),
            ],
            on_change=self.set_priority,
            expand=True
        )

        filter_priority = ft.Dropdown(
            hint_text="Filtrar por prioridade",
            options=[
                ft.dropdown.Option("Todas as prioridades"),
                ft.dropdown.Option("Baixa"),
                ft.dropdown.Option("Média"),
                ft.dropdown.Option("Alta"),
            ],
            on_change=self.filter_priority,
            expand=True
        )

        input_bar = ft.Row(
            controls=[input_task, input_priority, ft.FloatingActionButton(
                icon=ft.icons.ADD, bgcolor='#007BFF', on_click=lambda e: self.add(e, input_task, input_priority), expand=False)],
            spacing=10, height=50, alignment=ft.MainAxisAlignment.CENTER
        )

        tabs = ft.Tabs(
            selected_index=0, on_change=self.tabs_changed,
            tabs=[ft.Tab(text='Todos'), ft.Tab(text='Em andamento'), ft.Tab(text='Finalizados')]
        )

        tasks = self.tasks_container()

        filter_row = ft.Row(
            controls=[filter_priority],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

        self.page.add(input_bar, tabs, filter_row, tasks)

    def sync_offline_tasks(self):
        if self.is_connected():
            for task in self.offline_tasks:
                if task[1] == "deleted":
                    self.db_execute('DELETE FROM tasks WHERE name = ?', params=[task[0]])
                else:
                    self.db_execute('INSERT INTO tasks (name, status, priority) VALUES (?, ?, ?)',
                                    params=[task[0], task[1], task[2]])
            self.offline_tasks.clear()

ft.app(target=ToDo)
