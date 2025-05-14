import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import socket
import os
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime

class TestEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Электронный учитель v4.0")
        self.root.geometry("1000x700")
        
        # Данные теста
        self.test_data = {
            "title": "",
            "questions": []
        }
        self.teacher_version = {}
        self.student_version = {}
        self.user_answers = []
        self.user_mode = "teacher"
        self.default_port = 12345
        
        # Типы вопросов
        self.question_types = {
            "single": "Один правильный ответ",
            "multiple": "Несколько правильных ответов",
            "text": "Письменный ответ"
        }
        
        # GUI элементы
        self.create_top_frame()
        self.create_mode_selector()
        self.create_questions_frame()
    
    def create_top_frame(self):
        """Создает верхнюю панель с названием теста и кнопками"""
        self.top_frame = Frame(self.root)
        self.top_frame.pack(fill=X, padx=10, pady=5)
        
        # Название теста
        self.title_label = Label(self.top_frame, text="Название теста:")
        self.title_label.pack(side=LEFT, padx=5)
        
        self.title_entry = Entry(self.top_frame, width=50)
        self.title_entry.pack(side=LEFT, padx=5)
        
        # Кнопки для учителя
        self.teacher_buttons_frame = Frame(self.top_frame)
        self.teacher_buttons_frame.pack(side=LEFT, padx=10)
        
        self.add_question_btn = Button(self.teacher_buttons_frame, text="Добавить вопрос", command=self.add_question)
        self.add_question_btn.pack(side=LEFT, padx=2)
        
        self.save_test_btn = Button(self.teacher_buttons_frame, text="Сохранить тест", command=self.save_test_dialog)
        self.save_test_btn.pack(side=LEFT, padx=2)
        
        self.analyze_results_btn = Button(self.teacher_buttons_frame, text="Анализ ответов", command=self.analyze_results)
        self.analyze_results_btn.pack(side=LEFT, padx=2)
        
        # Кнопка для ученика
        self.save_results_btn = Button(self.top_frame, text="Сохранить результаты", command=self.save_results)
        
        # Меню
        self.create_menu()
    
    def create_mode_selector(self):
        """Создает переключатель режимов учитель/ученик"""
        mode_frame = Frame(self.root)
        mode_frame.pack(fill=X, padx=10, pady=5)
        
        Label(mode_frame, text="Режим работы:").pack(side=LEFT, padx=5)
        
        self.mode_var = StringVar(value="teacher")
        Radiobutton(mode_frame, text="Учитель", variable=self.mode_var, 
                   value="teacher", command=self.switch_mode).pack(side=LEFT, padx=5)
        Radiobutton(mode_frame, text="Ученик", variable=self.mode_var, 
                   value="student", command=self.switch_mode).pack(side=LEFT, padx=5)
    
    def create_questions_frame(self):
        """Создает область с вопросами"""
        self.questions_frame = Frame(self.root)
        self.questions_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        self.scrollbar = Scrollbar(self.questions_frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        
        self.canvas = Canvas(self.questions_frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.scrollbar.config(command=self.canvas.yview)
        
        self.inner_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=NW)
        
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
    
    def create_menu(self):
        menubar = Menu(self.root)
        
        # Меню Файл
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый тест", command=self.new_test)
        file_menu.add_command(label="Открыть тест", command=self.open_test)
        file_menu.add_command(label="Сохранить тест (учитель)", command=lambda: self.save_test(teacher_version=True))
        file_menu.add_command(label="Сохранить тест (ученик)", command=lambda: self.save_test(teacher_version=False))
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        # Меню Сеть
        network_menu = Menu(menubar, tearoff=0)
        network_menu.add_command(label="Отправить тест ученику", command=self.send_student_test)
        network_menu.add_command(label="Принять результаты", command=self.receive_results)
        network_menu.add_command(label="Настроить порт", command=self.configure_port)
        menubar.add_cascade(label="Сеть", menu=network_menu)
        
        self.root.config(menu=menubar)
    
    def configure_port(self):
        """Настраивает порт для сетевых операций"""
        port = simpledialog.askinteger("Настройка порта", "Введите номер порта:", initialvalue=self.default_port)
        if port and 1024 <= port <= 65535:
            self.default_port = port
            messagebox.showinfo("Успех", f"Порт изменен на {self.default_port}")
        elif port:
            messagebox.showerror("Ошибка", "Порт должен быть в диапазоне 1024-65535")
    
    def switch_mode(self):
        self.user_mode = self.mode_var.get()
        self.clear_answers()
        self.update_interface()
    
    def clear_answers(self):
        self.user_answers = []
    
    def update_interface(self):
        """Обновляет интерфейс в зависимости от режима"""
        if self.user_mode == "teacher":
            self.save_results_btn.pack_forget()
            self.teacher_buttons_frame.pack(side=LEFT, padx=10)
        else:
            self.teacher_buttons_frame.pack_forget()
            self.save_results_btn.pack(side=LEFT, padx=10)
        
        self.update_questions_list()
    
    def add_question(self):
        self.question_window = Toplevel(self.root)
        self.question_window.title("Добавить вопрос")
        self.question_window.geometry("600x500")
        
        # Тип вопроса
        Label(self.question_window, text="Тип вопроса:").pack(pady=5)
        self.question_type = StringVar(value="single")
        for key, text in self.question_types.items():
            Radiobutton(self.question_window, text=text, variable=self.question_type, 
                       value=key).pack(anchor=W, padx=20)
        
        # Текст вопроса
        Label(self.question_window, text="Текст вопроса:").pack(pady=5)
        self.question_text = Text(self.question_window, height=5, width=70)
        self.question_text.pack(pady=5)
        
        # Варианты ответов (для вопросов с выбором)
        self.options_frame = Frame(self.question_window)
        self.options_frame.pack(fill=X, pady=5)
        
        Label(self.options_frame, text="Варианты ответов (каждый с новой строки):").pack(anchor=W)
        self.options_text = Text(self.options_frame, height=10, width=70)
        self.options_text.pack(pady=5)
        
        # Правильные ответы
        self.correct_answers_frame = Frame(self.question_window)
        
        # Для вопросов с одним ответом
        self.single_answer_frame = Frame(self.correct_answers_frame)
        Label(self.single_answer_frame, text="Номер правильного ответа (начиная с 1):").pack(side=LEFT)
        self.correct_answer = Entry(self.single_answer_frame, width=5)
        self.correct_answer.pack(side=LEFT, padx=5)
        
        # Для вопросов с несколькими ответами
        self.multiple_answer_frame = Frame(self.correct_answers_frame)
        Label(self.multiple_answer_frame, text="Номера правильных ответов через запятую (начиная с 1):").pack(side=LEFT)
        self.correct_answers_entry = Entry(self.multiple_answer_frame, width=20)
        self.correct_answers_entry.pack(side=LEFT, padx=5)
        
        # Обработчик изменения типа вопроса
        self.question_type.trace_add("write", self.update_question_ui)
        self.update_question_ui()
        
        Button(self.question_window, text="Сохранить вопрос", command=self.save_question).pack(pady=10)
    
    def update_question_ui(self, *args):
        """Обновляет UI в зависимости от выбранного типа вопроса"""
        q_type = self.question_type.get()
        
        # Показываем/скрываем варианты ответов
        if q_type == "text":
            self.options_frame.pack_forget()
            self.correct_answers_frame.pack_forget()
        else:
            self.options_frame.pack(fill=X, pady=5)
            self.correct_answers_frame.pack(fill=X, pady=5)
            
            # Показываем нужный тип правильного ответа
            if q_type == "single":
                self.multiple_answer_frame.pack_forget()
                self.single_answer_frame.pack()
            else:
                self.single_answer_frame.pack_forget()
                self.multiple_answer_frame.pack()
    
    def save_question(self):
        question = self.question_text.get("1.0", END).strip()
        q_type = self.question_type.get()
        
        if not question:
            messagebox.showerror("Ошибка", "Введите текст вопроса!")
            return
        
        question_data = {
            "question": question,
            "type": q_type
        }
        
        if q_type in ["single", "multiple"]:
            options = [opt.strip() for opt in self.options_text.get("1.0", END).split("\n") if opt.strip()]
            
            if len(options) < 2:
                messagebox.showerror("Ошибка", "Добавьте хотя бы 2 варианта ответа!")
                return
            
            question_data["options"] = options
            
            if q_type == "single":
                correct = self.correct_answer.get().strip()
                
                if not correct:
                    messagebox.showerror("Ошибка", "Укажите правильный ответ!")
                    return
                
                try:
                    correct_idx = int(correct) - 1
                    if correct_idx < 0 or correct_idx >= len(options):
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректный номер правильного ответа!")
                    return
                
                question_data["correct"] = correct_idx
            else:
                correct_answers = self.correct_answers_entry.get().strip()
                
                if not correct_answers:
                    messagebox.showerror("Ошибка", "Укажите правильные ответы!")
                    return
                
                try:
                    correct_indices = [int(x.strip()) - 1 for x in correct_answers.split(",")]
                    for idx in correct_indices:
                        if idx < 0 or idx >= len(options):
                            raise ValueError
                except ValueError:
                    messagebox.showerror("Ошибка", "Некорректные номера правильных ответов!")
                    return
                
                question_data["correct"] = correct_indices
        
        self.test_data["questions"].append(question_data)
        self.update_questions_list()
        self.question_window.destroy()
    
    def update_questions_list(self):
        """Обновляет список вопросов"""
        # Очищаем фрейм
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        # Устанавливаем название теста
        self.test_data["title"] = self.title_entry.get()
        
        # Добавляем вопросы
        for i, question in enumerate(self.test_data["questions"], 1):
            question_frame = Frame(self.inner_frame, bd=1, relief=SOLID, padx=5, pady=5)
            question_frame.pack(fill=X, pady=5, padx=5)
            
            if self.user_mode == "teacher":
                # Режим учителя - просмотр вопросов
                Label(question_frame, text=f"Вопрос {i} ({self.question_types[question['type']]}): {question['question']}", 
                      font=('Arial', 10, 'bold')).pack(anchor=W)
                
                if question["type"] in ["single", "multiple"]:
                    correct = question.get("correct", [])
                    if question["type"] == "single":
                        correct_text = f"Правильный ответ: {question['options'][correct]} (№{correct + 1})"
                    else:
                        correct_text = "Правильные ответы: " + ", ".join(
                            f"{question['options'][idx]} (№{idx + 1})" for idx in correct)
                    
                    Label(question_frame, text=correct_text, fg="green").pack(anchor=W)
                
                # Кнопка удаления вопроса (только для учителя)
                delete_btn = Button(question_frame, text="Удалить", 
                                   command=lambda idx=i-1: self.delete_question(idx))
                delete_btn.pack(side=RIGHT, padx=5)
            else:
                # Режим ученика - прохождение теста
                if len(self.user_answers) < i:
                    if question["type"] == "text":
                        self.user_answers.append(StringVar())
                    else:
                        self.user_answers.append([])
                        for _ in question.get("options", []):
                            self.user_answers[-1].append(StringVar(value="0"))
                
                Label(question_frame, text=f"Вопрос {i}: {question['question']}", 
                      font=('Arial', 10, 'bold')).pack(anchor=W)
                
                if question["type"] == "text":
                    Entry(question_frame, textvariable=self.user_answers[i-1], width=70).pack(fill=X, pady=5)
                else:
                    for j, option in enumerate(question['options']):
                        if question["type"] == "single":
                            Radiobutton(
                                question_frame, 
                                text=option, 
                                variable=self.user_answers[i-1][0], 
                                value=str(j)
                            ).pack(anchor=W)
                        else:
                            Checkbutton(
                                question_frame,
                                text=option,
                                variable=self.user_answers[i-1][j],
                                onvalue="1",
                                offvalue="0"
                            ).pack(anchor=W)
        
        self.canvas.yview_moveto(0)
    
    def delete_question(self, index):
        """Удаляет вопрос по указанному индексу"""
        if 0 <= index < len(self.test_data["questions"]):
            self.test_data["questions"].pop(index)
            self.update_questions_list()
    
    def new_test(self):
        """Создает новый тест"""
        if self.test_data["questions"] or self.test_data["title"]:
            if not messagebox.askyesno("Подтверждение", "Вы уверены? Все несохраненные изменения будут потеряны."):
                return
        
        self.test_data = {"title": "", "questions": []}
        self.title_entry.delete(0, END)
        self.update_questions_list()
    
    def open_test(self):
        """Открывает тест из файла"""
        filepath = filedialog.askopenfilename(
            title="Открыть тест",
            filetypes=(("JSON файлы", "*.json"), ("Все файлы", "*.*"))
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "title" in data and "questions" in data:
                    self.test_data = data
                    self.title_entry.delete(0, END)
                    self.title_entry.insert(0, self.test_data["title"])
                    self.update_questions_list()
                else:
                    messagebox.showerror("Ошибка", "Некорректный формат файла теста!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def save_test_dialog(self):
        """Диалог сохранения теста"""
        if not self.test_data["questions"]:
            messagebox.showerror("Ошибка", "Тест не содержит вопросов!")
            return
        
        self.test_data["title"] = self.title_entry.get().strip()
        if not self.test_data["title"]:
            messagebox.showerror("Ошибка", "Введите название теста!")
            return
        
        # Создаем диалоговое окно для выбора типа сохранения
        choice_window = Toplevel(self.root)
        choice_window.title("Сохранить тест")
        choice_window.geometry("300x150")
        
        Label(choice_window, text="Выберите версию для сохранения:").pack(pady=10)
        
        Button(choice_window, text="Для учителя (с ответами)", 
              command=lambda: [self.save_test(teacher_version=True), choice_window.destroy()]).pack(fill=X, padx=20, pady=5)
        
        Button(choice_window, text="Для ученика (без ответов)", 
              command=lambda: [self.save_test(teacher_version=False), choice_window.destroy()]).pack(fill=X, padx=20, pady=5)
    
    def save_test(self, teacher_version=True):
        """Сохраняет тест в файл"""
        filepath = filedialog.asksaveasfilename(
            title="Сохранить тест",
            defaultextension=".json",
            filetypes=(("JSON файлы", "*.json"), ("Все файлы", "*.*"))
        )
        
        if filepath:
            try:
                if teacher_version:
                    data_to_save = self.test_data
                else:
                    self.prepare_versions()
                    data_to_save = self.student_version
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=4)
                
                messagebox.showinfo("Успех", "Тест успешно сохранен!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def prepare_versions(self):
        """Подготавливает версии теста для учителя и ученика"""
        self.teacher_version = self.test_data.copy()
        
        # Создаем версию для ученика (без правильных ответов)
        self.student_version = {
            "title": self.test_data["title"],
            "questions": []
        }
        
        for question in self.test_data["questions"]:
            student_question = {
                "question": question["question"],
                "type": question["type"]
            }
            
            if question["type"] in ["single", "multiple"]:
                student_question["options"] = question["options"]
            
            self.student_version["questions"].append(student_question)
    
    def save_results(self):
        """Сохраняет результаты тестирования"""
        if not self.test_data["questions"]:
            messagebox.showerror("Ошибка", "Нет вопросов для сохранения результатов!")
            return
        
        results = {
            "test_title": self.test_data["title"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "answers": []
        }
        
        for i, question in enumerate(self.test_data["questions"]):
            answer_data = {
                "question": question["question"],
                "type": question["type"],
                "answer": None
            }
            
            if question["type"] == "text":
                answer_data["answer"] = self.user_answers[i].get()
            else:
                if question["type"] == "single":
                    try:
                        answer_idx = int(self.user_answers[i][0].get())
                        answer_data["answer"] = [answer_idx]
                    except (ValueError, IndexError):
                        answer_data["answer"] = []
                else:
                    answer_data["answer"] = []
                    for j, var in enumerate(self.user_answers[i]):
                        if var.get() == "1":
                            answer_data["answer"].append(j)
            
            results["answers"].append(answer_data)
        
        filepath = filedialog.asksaveasfilename(
            title="Сохранить результаты",
            defaultextension=".json",
            filetypes=(("JSON файлы", "*.json"), ("Все файлы", "*.*"))
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Успех", "Результаты успешно сохранены!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить результаты:\n{str(e)}")
    
    def analyze_results(self):
        """Анализирует результаты тестирования"""
        filepath = filedialog.askopenfilename(
            title="Открыть файл с результатами",
            filetypes=(("JSON файлы", "*.json"), ("Все файлы", "*.*"))
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Загружаем оригинальный тест для сравнения
            test_file = filedialog.askopenfilename(
                title="Открыть оригинальный тест (с ответами)",
                filetypes=(("JSON файлы", "*.json"), ("Все файлы", "*.*"))
            )
            
            if not test_file:
                return
            
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # Сопоставляем вопросы теста с ответами
            total_questions = len(results["answers"])
            correct_answers = 0
            detailed_results = []
            score = 0
            max_score = total_questions
            
            for i, answer in enumerate(results["answers"]):
                if i >= len(test_data["questions"]):
                    break
                
                question = test_data["questions"][i]
                is_correct = False
                answer_score = 0
                
                if question["type"] == "text":
                    # Для текстовых ответов просто показываем ответ
                    detailed_results.append(
                        f"Вопрос {i+1}: {answer['question']}\n"
                        f"Тип: письменный ответ\n"
                        f"Ответ: {answer['answer']}\n"
                        f"(Текстовые ответы требуют ручной проверки)\n"
                    )
                else:
                    # Для вопросов с выбором проверяем правильность
                    if question["type"] == "single":
                        correct = [question["correct"]] if "correct" in question else []
                    else:
                        correct = question.get("correct", [])
                    
                    user_answer = answer.get("answer", [])
                    
                    if question["type"] == "single":
                        is_correct = user_answer == correct
                        answer_score = 1 if is_correct else 0
                    else:
                        # Для вопросов с несколькими ответами считаем частичные баллы
                        correct_count = len(correct)
                        user_correct = len(set(user_answer) & set(correct))
                        user_incorrect = len(set(user_answer) - set(correct))
                        
                        if correct_count > 0:
                            answer_score = max(0, (user_correct - user_incorrect) / correct_count)
                        is_correct = (answer_score == 1)
                    
                    if is_correct:
                        correct_answers += 1
                    
                    if question["type"] == "single":
                        question_type = "один правильный ответ"
                    else:
                        question_type = "несколько правильных ответов"
                    
                    detailed_results.append(
                        f"Вопрос {i+1}: {answer['question']}\n"
                        f"Тип: {question_type}\n"
                        f"Ответ ученика: {[question['options'][idx] for idx in answer['answer']] if answer['answer'] and 'options' in question else answer['answer']}\n"
                        f"Правильные ответы: {[question['options'][idx] for idx in correct] if correct and 'options' in question else correct}\n"
                        f"Баллы: {answer_score:.1f}/{1.0}\n"
                        f"Результат: {'Правильно' if is_correct else 'Неправильно'}\n"
                    )
                
                score += answer_score
            
            # Создаем окно с результатами
            result_window = Toplevel(self.root)
            result_window.title(f"Анализ результатов - {results['test_title']}")
            result_window.geometry("900x700")
            
            # Общая статистика
            stats_frame = Frame(result_window, bd=2, relief=GROOVE, padx=10, pady=10)
            stats_frame.pack(fill=X, padx=10, pady=10)
            
            Label(stats_frame, text=f"Тест: {results['test_title']}", font=('Arial', 12, 'bold')).pack(anchor=W)
            Label(stats_frame, text=f"Дата прохождения: {results['date']}").pack(anchor=W)
            
            if total_questions > 0:
                percentage = (score / max_score) * 100
                Label(stats_frame, 
                     text=f"Правильных ответов: {correct_answers} из {total_questions}", 
                     font=('Arial', 11)).pack(anchor=W)
                Label(stats_frame, 
                     text=f"Набрано баллов: {score:.1f} из {max_score}", 
                     font=('Arial', 11)).pack(anchor=W)
                Label(stats_frame, 
                     text=f"Процент выполнения: {percentage:.1f}%", 
                     font=('Arial', 11, 'bold')).pack(anchor=W)
            
            # Подробные результаты
            notebook = ttk.Notebook(result_window)
            notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)
            
            # Вкладка с текстовыми результатами
            text_frame = Frame(notebook)
            scrollbar = Scrollbar(text_frame)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            text = Text(text_frame, wrap=WORD, yscrollcommand=scrollbar.set)
            text.pack(fill=BOTH, expand=True)
            
            scrollbar.config(command=text.yview)
            
            for result in detailed_results:
                text.insert(END, result + "\n" + "-"*80 + "\n")
            
            text.config(state=DISABLED)
            notebook.add(text_frame, text="Подробные результаты")
            
            # Вкладка с графиком
            if total_questions > 0:
                try:
                    
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(["Правильные", "Неправильные"], [correct_answers, total_questions - correct_answers], 
                          color=['green', 'red'])
                    ax.set_title("Результаты тестирования")
                    ax.set_ylabel("Количество вопросов")
                    
                    chart_frame = Frame(notebook)
                    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=BOTH, expand=True)
                    
                    notebook.add(chart_frame, text="График")
                except ImportError:
                    pass
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось проанализировать результаты:\n{str(e)}")
    
    def send_student_test(self):
        """Отправляет тест ученику по сети"""
        if not self.test_data["questions"]:
            messagebox.showerror("Ошибка", "Нет вопросов для отправки!")
            return
        
        self.prepare_versions()
        
        ip = simpledialog.askstring("Отправка теста", "Введите IP адрес ученика:")
        if not ip:
            return
        
        try:
            self._send_file(ip, self.default_port, json.dumps(self.student_version).encode('utf-8'))
            messagebox.showinfo("Успех", f"Тест успешно отправлен ученику на порт {self.default_port}!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить тест:\n{str(e)}")
    
    def receive_results(self):
        """Принимает результаты от ученика по сети"""
        try:
            results = self._start_server(self.default_port)
            if results:
                # Сохраняем полученные результаты
                filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(json.loads(results.decode('utf-8')), f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Успех", f"Результаты успешно получены и сохранены в файл {filename}!")
                
                # Предлагаем сразу проанализировать результаты
                if messagebox.askyesno("Анализ", "Хотите проанализировать полученные результаты?"):
                    self.analyze_results()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить результаты:\n{str(e)}")
    
    def _send_file(self, ip, port, data):
        """Отправляет данные по сети"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.sendall(data)
    
    def _start_server(self, port, timeout=30):
        """Запускает сервер для приема данных"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.bind(('0.0.0.0', port))
            s.listen()
            
            messagebox.showinfo("Ожидание", f"Ожидание результатов на порту {port}...")
            
            conn, addr = s.accept()
            with conn:
                data = b''
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                
                return data

if __name__ == "__main__":
    root = Tk()
    app = TestEditor(root)
    root.mainloop()