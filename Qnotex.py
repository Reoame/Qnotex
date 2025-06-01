import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, font
import markdown2
import webbrowser
import os
import time
import re
import sys
import tempfile
import config



        
class MarkdownEditor:
    def get_resoure_path(self,relative_path): 
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS,relative_path).replace("\\", "/")
        return os.path.join(os.path.abspath("."), relative_path).replace("\\", "/")
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x700")
        self.root.title("Qnotex")

        try:
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件所在的目录
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, self.get_resoure_path("icon.ico"))
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {e}")

        self.root.configure(bg="#f5f7f9")
        self.text_font = font.Font(family="Segoe UI", size=12)
        self.preview_font = font.Font(family="Segoe UI", size=12)

        self.scroll_anim_id = None
        self.cursor_anim_id = None
        self.scroll_target = 0
        self.scroll_current = 0
        self.scroll_speed = 0.2
        self.cursor_visible = True

        # 当前打开的文件路径
        self.current_file = None
        self.temp_dir = tempfile.gettempdir()  # 获取系统临时目录

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 创建菜单栏
        self.create_menu()

        # 创建工具栏
        self.create_toolbar()

        # 创建主界面
        self.create_interface()

    def open_url_help(self):
        webbrowser.open("https://markdown.com.cn/basic-syntax/")

    def open_url_github(self):
        webbrowser.open("https://github.com/Reoame/Qnotex")
    def open_url_feedback(self):
        webbrowser.open("https://github.com/Reoame/Qnotex/issues")
    def on_closing(self):
        """处理窗口关闭事件"""
        # 取消所有动画
        if self.scroll_anim_id:
            self.root.after_cancel(self.scroll_anim_id)
        if self.cursor_anim_id:
            self.root.after_cancel(self.cursor_anim_id)

        # 询问用户是否退出
        if messagebox.askokcancel("退出", "确定要退出吗?记得保存代码！"):
            # 清理临时预览文件
            temp_file = os.path.join(self.temp_dir, "preview_temp.html")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"删除临时文件失败: {e}")

            # 关闭窗口
            self.root.destroy()


    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#f0f2f5", fg="#333", relief=tk.FLAT)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0, bg="#fff", fg="#333", bd=1, activebackground="#e6f7ff")
        file_menu.add_command(label="新建", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="导出HTML", command=self.export_html)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#fff", fg="#333", bd=1, activebackground="#e6f7ff")
        edit_menu.add_command(label="撤销", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="复制", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="粘贴", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self.find_text, accelerator="Ctrl+F")
        menubar.add_cascade(label="编辑", menu=edit_menu)

        # 格式菜单
        format_menu = tk.Menu(menubar, tearoff=0, bg="#fff", fg="#333", bd=1, activebackground="#e6f7ff")
        format_menu.add_command(label="标题 1", command=lambda: self.insert_format("# "))
        format_menu.add_command(label="标题 2", command=lambda: self.insert_format("## "))
        format_menu.add_command(label="标题 3", command=lambda: self.insert_format("### "))
        format_menu.add_separator()
        format_menu.add_command(label="粗体", command=lambda: self.insert_format("**", "**"))
        format_menu.add_command(label="斜体", command=lambda: self.insert_format("*", "*"))
        format_menu.add_command(label="删除线", command=lambda: self.insert_format("~~", "~~"))
        format_menu.add_separator()
        format_menu.add_command(label="链接", command=lambda: self.insert_format("[", "](https://)"))
        format_menu.add_command(label="图片", command=lambda: self.insert_format("![", "](image.png)"))
        format_menu.add_command(label="代码", command=lambda: self.insert_format("`", "`"))
        format_menu.add_command(label="代码块", command=lambda: self.insert_format("```\n", "\n```"))
        format_menu.add_command(label="引用", command=lambda: self.insert_format("> "))
        format_menu.add_command(label="无序列表", command=lambda: self.insert_format("- "))
        format_menu.add_command(label="有序列表", command=lambda: self.insert_format("1. "))
        menubar.add_cascade(label="格式", menu=format_menu)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0, bg="#fff", fg="#333", bd=1, activebackground="#e6f7ff")
        view_menu.add_command(label="预览Markdown", command=self.preview_markdown)
        view_menu.add_command(label="刷新预览", command=self.refresh_preview)
    
        menubar.add_cascade(label="视图", menu=view_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0, bg="#fff", fg="#333", bd=1, activebackground="#e6f7ff")
        help_menu.add_command(label="Markdown语法", command=self.open_url_help)
        help_menu.add_command(label="Github", command=self.open_url_github)
        help_menu.add_command(label="反馈", command=self.open_url_feedback)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

        # 绑定快捷键
        self.root.bind_all("<Control-n>", lambda event: self.new_file())
        self.root.bind_all("<Control-o>", lambda event: self.open_file())
        self.root.bind_all("<Control-s>", lambda event: self.save_file())
        self.root.bind_all("<Control-f>", lambda event: self.find_text())

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bd=0, relief=tk.FLAT, bg="#e1e8ed", height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        # 文件操作按钮
        new_btn = tk.Button(toolbar, text="📄 新建", command=self.new_file,
                            bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                            font=("Segoe UI", 10), relief=tk.FLAT,
                            activebackground="#d1e0ed")
        new_btn.pack(side=tk.LEFT, padx=2, pady=2)

        open_btn = tk.Button(toolbar, text="📂 打开", command=self.open_file,
                             bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                             font=("Segoe UI", 10), relief=tk.FLAT,
                             activebackground="#d1e0ed")
        open_btn.pack(side=tk.LEFT, padx=2, pady=2)

        save_btn = tk.Button(toolbar, text="💾 保存", command=self.save_file,
                             bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                             font=("Segoe UI", 10), relief=tk.FLAT,
                             activebackground="#d1e0ed")
        save_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # 分隔符
        tk.Frame(toolbar, width=10, height=1, bg="#e1e8ed").pack(side=tk.LEFT, padx=5)

        # 格式按钮
        bold_btn = tk.Button(toolbar, text="B", command=lambda: self.insert_format("**", "**"),
                             font=("Segoe UI", 10, "bold"), width=3, height=1,
                             bg="#d6eaf8", fg="#2874a6", bd=0,
                             activebackground="#aed6f1")
        bold_btn.pack(side=tk.LEFT, padx=2, pady=2)

        italic_btn = tk.Button(toolbar, text="I", command=lambda: self.insert_format("*", "*"),
                               font=("Segoe UI", 10, "italic"), width=3, height=1,
                               bg="#d6eaf8", fg="#2874a6", bd=0,
                               activebackground="#aed6f1")
        italic_btn.pack(side=tk.LEFT, padx=2, pady=2)

        code_btn = tk.Button(toolbar, text="</>", command=lambda: self.insert_format("`", "`"),
                             font=("Segoe UI", 10), width=3, height=1,
                             bg="#d6eaf8", fg="#2874a6", bd=0,
                             activebackground="#aed6f1")
        code_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # 分隔符
        tk.Frame(toolbar, width=10, height=1, bg="#e1e8ed").pack(side=tk.LEFT, padx=5)

        # 标题按钮
        h1_btn = tk.Button(toolbar, text="H1", command=lambda: self.insert_format("# "),
                           font=("Segoe UI", 9, "bold"), width=2, height=1,
                           bg="#e8f8f5", fg="#1d8348", bd=0,
                           activebackground="#abebc6")
        h1_btn.pack(side=tk.LEFT, padx=2, pady=2)

        h2_btn = tk.Button(toolbar, text="H2", command=lambda: self.insert_format("## "),
                           font=("Segoe UI", 9, "bold"), width=2, height=1,
                           bg="#e8f8f5", fg="#1d8348", bd=0,
                           activebackground="#abebc6")
        h2_btn.pack(side=tk.LEFT, padx=2, pady=2)

        h3_btn = tk.Button(toolbar, text="H3", command=lambda: self.insert_format("### "),
                           font=("Segoe UI", 9, "bold"), width=2, height=1,
                           bg="#e8f8f5", fg="#1d8348", bd=0,
                           activebackground="#abebc6")
        h3_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # 分隔符
        tk.Frame(toolbar, width=10, height=1, bg="#e1e8ed").pack(side=tk.LEFT, padx=5)

        # 预览按钮
        preview_btn = tk.Button(toolbar, text="👁️ 预览", command=self.preview_markdown,
                                bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                                font=("Segoe UI", 10), relief=tk.FLAT,
                                activebackground="#d1e0ed")
        preview_btn.pack(side=tk.LEFT, padx=2, pady=2)

        refresh_btn = tk.Button(toolbar, text="🔄 刷新", command=self.refresh_preview,
                                bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                                font=("Segoe UI", 10), relief=tk.FLAT,
                                activebackground="#d1e0ed")
        refresh_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # 导出按钮
        export_btn = tk.Button(toolbar, text="💻 导出", command=self.export_html,
                               bg="#e1e8ed", fg="#2c3e50", bd=0, padx=10, pady=5,
                               font=("Segoe UI", 10), relief=tk.FLAT,
                               activebackground="#d1e0ed")
        export_btn.pack(side=tk.LEFT, padx=2, pady=2)

    def create_interface(self):
        # 创建分割窗口
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8,
                                           sashrelief=tk.RAISED, bg="#d6dbdf", bd=0)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 左侧编辑区框架
        editor_frame = tk.Frame(self.paned_window, bg="#fff", bd=0)
        editor_header = tk.Frame(editor_frame, bg="#3498db", height=30)
        editor_header.pack(fill=tk.X)
        tk.Label(editor_header, text="Markdown 编辑器", bg="#3498db", fg="white",
                 font=("Segoe UI", 10, "bold"), padx=10, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 编辑区
        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=self.text_font,
            undo=True,
            padx=15,
            pady=15,
            bg="#ffffff",
            fg="#2c3e50",
            insertbackground="#3498db",
            selectbackground="#d6eaf8",
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor="#d6dbdf",
            highlightbackground="#d6dbdf"
        )
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(editor_frame)

        # 右侧预览区框架
        preview_frame = tk.Frame(self.paned_window, bg="#fff", bd=0)
        preview_header = tk.Frame(preview_frame, bg="#2ecc71", height=30)
        preview_header.pack(fill=tk.X)
        tk.Label(preview_header, text="HTML 预览", bg="#2ecc71", fg="white",
                 font=("Segoe UI", 10, "bold"), padx=10, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 预览区
        self.preview = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            state=tk.NORMAL,
            bg="#ffffff",
            fg="#2c3e50",
            font=self.preview_font,
            padx=15,
            pady=15,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor="#d6dbdf",
            highlightbackground="#d6dbdf"
        )
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.config(state=tk.DISABLED)
        self.paned_window.add(preview_frame)

        # 设置初始分割比例
        self.paned_window.paneconfig(editor_frame, width=600)
        self.paned_window.paneconfig(preview_frame, width=600)

        # 状态栏
        status_frame = tk.Frame(self.root, bg="#34495e", height=24, bd=0)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))

        self.status = tk.Label(
            status_frame,
            text="就绪 | 行: 1, 列: 0",
            bd=0,
            relief=tk.FLAT,
            anchor=tk.W,
            bg="#34495e",
            fg="#ecf0f1",
            font=("Segoe UI", 9),
            padx=10
        )
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.file_info = tk.Label(
            status_frame,
            text="未保存的文件",
            bd=0,
            relief=tk.FLAT,
            anchor=tk.E,
            bg="#34495e",
            fg="#bdc3c7",
            font=("Segoe UI", 9),
            padx=10
        )
        self.file_info.pack(side=tk.RIGHT)

        # 绑定事件
        self.editor.bind("<KeyRelease>", self.update_status)
        self.editor.bind("<ButtonRelease-1>", self.update_status)

        # 添加初始提示
        self.editor.insert(tk.END, "# 欢迎使用Qnote Markdown编辑器\n\n")
        self.editor.insert(tk.END, "## 这是一个现代化的Markdown编辑工具\n\n")
        self.editor.insert(tk.END, "开始编写您的Markdown文档...\n\n")
        self.editor.insert(tk.END, "**功能特性**:\n")
        self.editor.insert(tk.END, "- 实时预览\n")
        self.editor.insert(tk.END, "- 语法高亮\n")
        self.editor.insert(tk.END, "- 格式工具栏\n")
        self.editor.insert(tk.END, "- 导出HTML\n")

        self.refresh_preview()

    def new_file(self):
        self.editor.delete(1.0, tk.END)
        self.current_file = None
        self.update_status("新建文件")
        self.file_info.config(text="未保存的文件")
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.config(state=tk.DISABLED)

        # 添加初始提示
        self.editor.insert(tk.END, "# 新文档\n\n")
        self.editor.insert(tk.END, "开始编写您的Markdown内容...\n")

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.editor.delete(1.0, tk.END)
                    self.editor.insert(tk.END, content)
                    self.current_file = file_path
                    self.update_status(f"已打开: {file_path}")
                    self.file_info.config(text=f"文件: {os.path.basename(file_path)}")
                    self.refresh_preview()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件:\n{str(e)}")

    def save_file(self):
        if self.current_file:
            try:
                content = self.editor.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                self.update_status(f"已保存: {self.current_file}")
                self.file_info.config(text=f"文件: {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败:\n{str(e)}")
        else:
            self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            self.current_file = file_path
            self.save_file()

    def export_html(self):
        if not self.editor.get(1.0, tk.END).strip():
            messagebox.showwarning("警告", "内容为空，无法导出HTML")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML文件", "*.html"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                markdown_text = self.editor.get(1.0, tk.END)
                html = self.convert_to_html(markdown_text)

                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(html)
                self.update_status(f"已导出HTML: {file_path}")
                messagebox.showinfo("导出成功", f"HTML文件已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出HTML失败:\n{str(e)}")

    def convert_to_html(self, markdown_text):
        html = markdown2.markdown(markdown_text)
        
        # 添加基本的HTML结构
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QnotexBuild</title>
    <link rel="stylesheet" href={config.url}>
</head>
<body>
{html}
</body>
</html>"""

    def preview_markdown(self):
        markdown_text = self.editor.get(1.0, tk.END).strip()
        if not markdown_text:
            messagebox.showwarning("预览", "内容为空，无法预览")
            return

        html = self.convert_to_html(markdown_text)

        # 保存临时HTML文件到临时目录
        temp_file = os.path.join(self.temp_dir, "preview_temp.html")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html)

        # 在浏览器中打开预览
        webbrowser.open(f"file://{temp_file}")
        self.update_status("在浏览器中打开预览")

    def refresh_preview(self):
        markdown_text = self.editor.get(1.0, tk.END).strip()
        if not markdown_text:
            self.preview.config(state=tk.NORMAL)
            self.preview.delete(1.0, tk.END)
            self.preview.insert(tk.END, "没有内容可预览")
            self.preview.config(state=tk.DISABLED)
            return

        html = self.convert_to_html(markdown_text)

        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, html)
        self.preview.config(state=tk.DISABLED)
        self.update_status("预览已刷新")

    def update_status(self, event=None):
        if isinstance(event, str):
            status_text = event
            self.status.config(text=status_text)
            return

        if self.current_file:
            file_info = f" | 文件: {os.path.basename(self.current_file)}"
        else:
            file_info = " | 未保存的文件"

        # 获取光标位置
        cursor_index = self.editor.index(tk.INSERT)
        line, col = cursor_index.split('.')

        # 获取总行数
        total_lines = self.editor.index('end-1c').split('.')[0]

        # 获取选中的文本
        try:
            selected = len(self.editor.get(tk.SEL_FIRST, tk.SEL_LAST))
        except:
            selected = 0

        status_text = f"就绪{file_info} | 行: {line}/{total_lines}, 列: {col} | 选中: {selected}字符"
        self.status.config(text=status_text)

    def undo(self):
        try:
            self.editor.edit_undo()
        except:
            pass

    def redo(self):
        try:
            self.editor.edit_redo()
        except:
            pass

    def cut(self):
        self.editor.event_generate("<<Cut>>")

    def copy(self):
        self.editor.event_generate("<<Copy>>")

    def paste(self):
        self.editor.event_generate("<<Paste>>")

    def find_text(self):
        # 创建查找窗口
        find_window = tk.Toplevel(self.root)
        find_window.title("查找")
        find_window.geometry("400x180")
        find_window.transient(self.root)
        find_window.grab_set()
        find_window.configure(bg="#f5f7f9")

        tk.Label(find_window, text="查找内容:", bg="#f5f7f9", fg="#2c3e50",
                 font=("Segoe UI", 10)).pack(pady=(15, 5), padx=15, anchor=tk.W)

        entry_frame = tk.Frame(find_window, bg="#f5f7f9")
        entry_frame.pack(fill=tk.X, padx=15)

        find_entry = tk.Entry(entry_frame, width=40, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        find_entry.pack(fill=tk.X, padx=0, pady=5)
        find_entry.focus_set()

        # 查找按钮
        def find():
            text = find_entry.get()
            if not text:
                return

            content = self.editor.get(1.0, tk.END)
            start_index = self.editor.index(tk.INSERT)

            # 从当前光标位置开始查找
            pos = content.find(text, self.editor.index(tk.INSERT))

            if pos == -1:
                messagebox.showinfo("查找", "未找到匹配项")
                return

            # 计算行和列
            line = content.count('\n', 0, pos) + 1
            col = pos - content.rfind('\n', 0, pos)

            # 选中找到的文本
            start_index = f"{line}.{col}"
            end_index = f"{line}.{col + len(text)}"
            self.editor.tag_remove(tk.SEL, 1.0, tk.END)
            self.editor.tag_add(tk.SEL, start_index, end_index)
            self.editor.mark_set(tk.INSERT, end_index)
            self.editor.see(start_index)

            self.update_status(f"找到: {text}")

        btn_frame = tk.Frame(find_window, bg="#f5f7f9")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="查找", command=find, width=10,
                  bg="#3498db", fg="white", font=("Segoe UI", 9), bd=0,
                  activebackground="#2980b9").pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="关闭", command=find_window.destroy, width=10,
                  bg="#95a5a6", fg="white", font=("Segoe UI", 9), bd=0,
                  activebackground="#7f8c8d").pack(side=tk.LEFT, padx=10)

    def insert_format(self, prefix, suffix=None):
        # 如果有选中文本，在选中文本前后添加格式
        try:
            start = self.editor.index(tk.SEL_FIRST)
            end = self.editor.index(tk.SEL_LAST)
            selected_text = self.editor.get(start, end)

            self.editor.delete(start, end)
            self.editor.insert(start, prefix + selected_text + (suffix if suffix else ""))
        except:
            # 没有选中文本，直接插入格式
            cursor_pos = self.editor.index(tk.INSERT)
            self.editor.insert(cursor_pos, prefix + (suffix if suffix else ""))

            # 将光标移动到格式中间
            if suffix:
                new_pos = self.editor.index(f"{cursor_pos} + {len(prefix)}c")
                self.editor.mark_set(tk.INSERT, new_pos)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MarkdownEditor(root)
        root.mainloop()
    except Exception as e:
        # 将错误信息写入日志文件
        with open("error.log", "w") as f:
            f.write(f"程序崩溃: {str(e)}\n")
            import traceback

            traceback.print_exc(file=f)

        # 显示错误消息
        messagebox.showerror("程序错误", f"程序发生错误: {str(e)}\n详细信息已保存到error.log文件")  