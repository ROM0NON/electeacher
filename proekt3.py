import json
import socket
import os
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime

class TestEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Тестовый редактор v2.1 (Учитель+Ученик)")
        self.root.geometry("900x650")
        
        # Данные теста
        self.test_data = {
            "title": "",
            "questions": []
        }
        self.user_answers = []
        self.user_mode = "teacher"  # По умолчанию режим учителя
        
        # GUI элементы
        self.create_widgets()
        self.create_mode_selector()
        
    def create_mode_selector(self):
        mode_frame = Frame(self.root)
        mode_frame.pack(pady=10)
        
        Label(mode_frame, text="Режим работы:").pack(side=LEFT, padx=5)
        
        self.mode_var = StringVar(value="teacher")
        Radiobutton(mode_frame, text="Учитель", variable=self.mode_var, 
                   value="teacher", command=self.switch_mode).pack(side=LEFT, padx=5)
        Radiobutton(mode_frame, text="Ученик", variable=self.mode_var, 
                   value="student", command=self.switch_mode).pack(side=LEFT, padx=5)
    
    def switch_mode(self):
        self.user_mode = self.mode_var.get()
        self.clear_answers()  # Очищаем предыдущие ответы при смене режима
        self.update_interface()
    
    def clear_answers(self):
        self.user_answers = []
    
    def update_interface(self):
        # Скрываем/показываем элементы в зависимости от режима
        if self.user_mode == "teacher":
            self.title_label.pack(pady=5)
            self.title_entry.pack(pady=5)
            self.add_question_btn.pack(pady=10)
            self.save_results_btn.pack_forget()
            self.questions_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        else:
            self.title_label.pack_forget()
            self.title_entry.pack_forget()
            self.add_question_btn.pack_forget()
            self.save_results_btn.pack(pady=10)
            self.questions_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.update_questions_list()
    
    def create_widgets(self):
        # Панель меню
        menubar = Menu(self.root)
        
        # Меню Файл
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый тест", command=self.new_test)
        file_menu.add_command(label="Открыть тест", command=self.open_test)
        file_menu.add_command(label="Сохранить тест", command=self.save_test)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню Сеть
        network_menu = Menu(menubar, tearoff=0)
        network_menu.add_command(label="Отправить файл", command=self.send_file)
        network_menu.add_command(label="Принять файл", command=self.receive_file)
        menubar.add_cascade(label="Сеть", menu=network_menu)
        
        self.root.config(menu=menubar)
        
        # Основные элементы
        self.title_label = Label(self.root, text="Название теста:")
        self.title_entry = Entry(self.root, width=50)
        
        self.add_question_btn = Button(self.root, text="Добавить вопрос", command=self.add_question)
        self.save_results_btn = Button(self.root, text="Сохранить результаты", command=self.save_results)
        
        self.questions_frame = Frame(self.root)
        
        # Инициализация интерфейса
        self.update_interface()
    
    def new_test(self):
        self.test_data = {"title": "", "questions": []}
        self.title_entry.delete(0, END)
        self.clear_answers()  # Очищаем ответы при создании нового теста
        self.update_questions_list()
    
    def open_test(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON файлы", "*.json")])
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.test_data = json.load(f)
                self.title_entry.delete(0, END)
                self.title_entry.insert(0, self.test_data.get("title", ""))
                self.clear_answers()  # Очищаем ответы при загрузке нового теста
                self.update_questions_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def add_question(self):
        self.question_window = Toplevel(self.root)
        self.question_window.title("Новый вопрос")
        self.question_window.geometry("500x400")
        
        # Поля для вопроса
        Label(self.question_window, text="Текст вопроса:").pack(pady=5)
        self.question_text = Text(self.question_window, height=5, width=50)
        self.question_text.pack(pady=5)
        
        # Варианты ответов
        Label(self.question_window, text="Варианты ответов (каждый с новой строки):").pack(pady=5)
        self.options_text = Text(self.question_window, height=10, width=50)
        self.options_text.pack(pady=5)
        
        # Правильный ответ
        Label(self.question_window, text="Номер правильного ответа (начиная с 1):").pack(pady=5)
        self.correct_answer = Entry(self.question_window, width=5)
        self.correct_answer.pack(pady=5)
        
        Button(self.question_window, text="Сохранить вопрос", command=self.save_question).pack(pady=10)
    
    def save_question(self):
        question = self.question_text.get("1.0", END).strip()
        options = [opt.strip() for opt in self.options_text.get("1.0", END).split("\n") if opt.strip()]
        correct = self.correct_answer.get().strip()
        
        if not question or len(options) < 2 or not correct:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
            
        try:
            correct_idx = int(correct) - 1
            if correct_idx < 0 or correct_idx >= len(options):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный номер правильного ответа!")
            return
            
        self.test_data["questions"].append({
            "question": question,
            "options": options,
            "correct": correct_idx
        })
        
        self.update_questions_list()
        self.question_window.destroy()
    
    def update_questions_list(self):
        # Очищаем фрейм
        for widget in self.questions_frame.winfo_children():
            widget.destroy()
            
        # Добавляем вопросы
        for i, question in enumerate(self.test_data["questions"], 1):
            question_frame = Frame(self.questions_frame, bd=1, relief=SOLID)
            question_frame.pack(fill=X, pady=5, padx=5)
            
            if self.user_mode == "teacher":
                # Режим учителя - просмотр вопросов
                Label(question_frame, text=f"Вопрос {i}: {question['question']}").pack(anchor=W)
                Label(question_frame, text=f"Правильный ответ: {question['options'][question['correct']]}").pack(anchor=W)
            else:
                # Режим ученика - прохождение теста
                if len(self.user_answers) < i:
                    self.user_answers.append(StringVar(value="-1"))  # Добавляем только если нужно
                
                Label(question_frame, text=f"Вопрос {i}: {question['question']}").pack(anchor=W)
                
                # Варианты ответов
                for j, option in enumerate(question['options']):
                    Radiobutton(
                        question_frame, 
                        text=option, 
                        variable=self.user_answers[i-1], 
                        value=str(j)
                    ).pack(anchor=W)
    
    def save_results(self):
        if not self.test_data.get("questions"):
            messagebox.showerror("Ошибка", "Сначала загрузите тест!")
            return
            
        # Проверяем, все ли вопросы отвечены
        unanswered = [i+1 for i, ans in enumerate(self.user_answers) if ans.get() == "-1"]

        if unanswered:
            messagebox.showerror("Ошибка", f"Ответьте на все вопросы! Не отвечены: {unanswered}")
            return
            
        # Собираем результаты
        student_name = simpledialog.askstring("Результаты", "Введите ваше имя:")
        if not student_name:
            messagebox.showerror("Ошибка", "Необходимо ввести имя!")
            return
            
        results = {
            "test_title": self.test_data.get("title", "Без названия"),
            "student_name": student_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "answers": [],
            "score": 0
        }
        
        # Проверяем ответы
        correct_count = 0
        for i, (question, answer_var) in enumerate(zip(self.test_data["questions"], self.user_answers)):
            user_answer = int(answer_var.get())
            is_correct = (user_answer == question["correct"])
            if is_correct:
                correct_count += 1
                
            results["answers"].append({
                "question": question["question"],
                "user_answer": question["options"][user_answer],
                "correct_answer": question["options"][question["correct"]],
                "is_correct": is_correct
            })
        
        results["score"] = f"{correct_count}/{len(self.test_data['questions'])}"
        
        # Сохраняем результаты
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json")],
            initialfile=f"results_{student_name}.json"
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Успех", f"Результаты сохранены!\nВаш результат: {results['score']}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить результаты: {str(e)}")
    
    def save_test(self):
        self.test_data["title"] = self.title_entry.get().strip()
        if not self.test_data["title"]:
            messagebox.showerror("Ошибка", "Введите название теста!")
            return
            
        if not self.test_data["questions"]:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один вопрос!")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.test_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Успех", "Тест успешно сохранен!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def send_file(self):
        if not self.test_data["questions"]:
            messagebox.showerror("Ошибка", "Сначала создайте или загрузите тест!")
            return
            
        self.send_window = Toplevel(self.root)
        self.send_window.title("Отправить файл")
        self.send_window.geometry("400x200")
        
        Label(self.send_window, text="IP-адрес получателя:").pack(pady=5)
        self.ip_entry = Entry(self.send_window, width=20)
        self.ip_entry.pack(pady=5)
        self.ip_entry.insert(0, "192.168.1.")
        
        Label(self.send_window, text="Порт (по умолчанию 12345):").pack(pady=5)
        self.port_entry = Entry(self.send_window, width=10)
        self.port_entry.pack(pady=5)
        self.port_entry.insert(0, "12345")
        
        Button(self.send_window, text="Отправить", command=self._send_file).pack(pady=10)
    
    def _send_file(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом!")
            return
            
        # Сначала сохраняем во временный файл
        temp_file = "temp_test.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f)
            
        # Отправляем файл
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                with open(temp_file, "rb") as f:
                    s.sendfile(f)
            messagebox.showinfo("Успех", "Файл успешно отправлен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить файл: {str(e)}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        self.send_window.destroy()
    
    def receive_file(self):
        self.receive_window = Toplevel(self.root)
        self.receive_window.title("Принять файл")
        self.receive_window.geometry("400x200")
        
        Label(self.receive_window, text="Порт для прослушивания (по умолчанию 12345):").pack(pady=5)
        self.port_entry_receive = Entry(self.receive_window, width=10)
        self.port_entry_receive.pack(pady=5)
        self.port_entry_receive.insert(0, "12345")
        
        self.status_label = Label(self.receive_window, text="Ожидание подключения...")
        self.status_label.pack(pady=10)
        
        Button(self.receive_window, text="Начать прослушивание", command=self._start_server).pack(pady=10)
    
    def _start_server(self):
        port = self.port_entry_receive.get().strip()
        
        if not port:
            messagebox.showerror("Ошибка", "Укажите порт!")
            return
            
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом!")
            return
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                s.listen(1)
                self.status_label.config(text=f"Ожидание подключения на порту {port}...")
                
                conn, addr = s.accept()
                self.status_label.config(text=f"Подключено: {addr[0]}")
                
                temp_file = "received_test.json"
                with open(temp_file, "wb") as f:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        f.write(data)
                
                # Загружаем полученный тест
                with open(temp_file, "r", encoding="utf-8") as f:
                    self.test_data = json.load(f)
                self.title_entry.delete(0, END)
                self.title_entry.insert(0, self.test_data.get("title", ""))
                self.clear_answers()  # Очищаем ответы при получении нового теста
                self.update_questions_list()
                
                messagebox.showinfo("Успех", "Тест успешно получен и загружен!")
                self.receive_window.destroy()
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сервера: {str(e)}")

if __name__ == "__main__":
    root = Tk()
    app = TestEditor(root)
    root.mainloop()