"""
プログラミングのクイズアプリ
"""


import time
import json
import tkinter as tk
from tkinter import ttk

from chat_api import ask_chat_gpt
from mock_ev3 import check_runtime_errors_with_mock


def on_click(event):
    global line_number
    index = text_widget.index(f"@{event.x},{event.y}")
    line_number = int(index.split('.')[0])
    
    if line_number in editable_lines:
        current_text = text_widget.get(f"{line_number}.0", f"{line_number}.end")
        entry_var.set(current_text)

        bbox = text_widget.bbox(f"{line_number}.0")
        if bbox:
            x, y, width, height = bbox
            entry_widget.place(x=780+24, y=y+62)
            entry_widget.focus()
            entry_widget.select_range(0, tk.END)
            entry_widget.icursor(tk.END)
    else:
        entry_widget.place_forget()

def on_entry_change(*args):
    current_text = entry_var.get()
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(f"{line_number}.0", f"{line_number}.end")
    text_widget.insert(f"{line_number}.0", current_text)
    text_widget.config(state=tk.DISABLED)

def on_tab(event):
    entry_widget.insert(tk.INSERT, " " * 4)
    return "break"

def on_enter(event):
    entry_widget.place_forget()


# コンテンツ
def start_timer(seconds):
    global start_time, timer_started
    start_time = time.time()
    timer_started = True
    progress_bar['maximum'] = seconds
    progress_var.set(seconds)
    update_timer()


def update_timer():    
    global timer_started, last_hinted_time
    if not timer_started:
        return
    
    elapsed_time = time.time() - start_time
    time_left = max(time_limit - elapsed_time, 0)
    progress_var.set(time_left)

    # ヒントを表示
    if hinted_count < MAX_HINT_COUNT and elapsed_time - last_hinted_time > HINT_INTERVAL:
    #if not is_showing_hint and time_left <= time_limit - 10:
        hint_button.place(x=20, y=400)  
        last_hinted_time = elapsed_time

    root.after(100, update_timer)


def update_quiz(data):
    global instruction, true_code, default_code, editable_lines, time_limit, hinted_count, last_hinted_time
    # extract data
    code_list = data.get('code', [])
    instruction_list = data.get('instruction', [])
    editable_lines = data.get('editable_lines', [])
    content = data.get('content', [])
    time_limit = data.get('time_limit', 60)
    true_code = "\n".join(code_list)

    # コードの穴埋め実行
    for item in content:
        line, default_text = item.get('line'), item.get('default', "")
        code_list[line-1] = default_text
    
    # 平文に変換
    default_code = "\n".join(code_list)
    instruction = "\n".join(instruction_list)
    
    update_code(default_code)
    update_instruction(instruction)
    update_tags(content)
    update_answers(content)
    start_timer(time_limit)

    hinted_count = 0
    last_hinted_time = 0
    entry_widget.place_forget()


def update_code(code):
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, code)
    text_widget.tag_configure("editable", background="white", foreground="black")
    text_widget.tag_configure("non_editable", background="white", foreground="black")
    text_widget.tag_configure("highlight", background="yellow")
    for i in range(1, int(text_widget.index(tk.END).split('.')[0])):
        if i not in editable_lines:
            text_widget.tag_add("non_editable", f"{i}.0", f"{i}.end")
        else:
            text_widget.tag_add("editable", f"{i}.0", f"{i}.end")
    text_widget.config(state=tk.DISABLED)


def update_tags(content):
    tag_widget.config(state=tk.NORMAL)
    tag_widget.delete("1.0", tk.END)
    lines = text_widget.get("1.0", tk.END).count("\n")
    lines_with_tag = [v['line'] for v in content]
    for i in range(1, lines + 1):
        if i in lines_with_tag:
            tag = next(iter([v['tag'] for v in content if v['line'] == i]), "")
            tag_widget.insert(tk.END, f"{tag}\n", "right")
        else:
            tag_widget.insert(tk.END, f"\n", "right")
    tag_widget.config(state=tk.DISABLED)


def update_instruction(new_content):
    instruction_text.config(state=tk.NORMAL)
    instruction_text.delete('1.0', tk.END)
    instruction_text.insert(tk.END, new_content)
    instruction_text.config(state=tk.DISABLED)


def update_answers(content):
    global correct_answers
    correct_answers = {}
    for item in content:
        line, answer = item.get('line', -1), item.get('answer', "")
        if line != -1 and answer != "":
            correct_answers[line] = answer


def check_answer():
    global timer_started
    elapsed_time = time.time() - start_time
    entry_widget.place_forget()
    incorrect_line_number = 0

    all_correct = True
    for line, answer in correct_answers.items():
        user_input = text_widget.get(f"{line}.0", f"{line}.end")
        # check code 
        if user_input.replace(" ", "") != answer.replace(" ", ""):
            incorrect_line_number = line
            all_correct = False
            break
    
    if all_correct:
        result_label.config(text=f"全て正解です！\n経過時間:{elapsed_time:.1f}秒", fg="green")
        timer_started = False
        hint_button.place_forget()
        hint_label.place_forget()
        error_label.place_forget()
    else:
        # 不正解の場合、エラーを検出してユーザーにフィードバック
        result_label.config(text="不正解があります。もう一度確認してください。", fg="red")

        user_code = text_widget.get("1.0", tk.END)
        is_valid, message, line = check_runtime_errors_with_mock(user_code)
        if not is_valid:
            print(f"error detected in user code (line:{line}): {message}")  
            error_label.config(text=f"Line {line}: {message}", fg="red")
            highlight_line(line, 5000)
            error_history.append((line, message))
        else:          
            error_label.config(text=f"Line {incorrect_line_number}: インストラクションに合っていません。", fg="red")
            highlight_line(incorrect_line_number, 5000)
            error_history.append((incorrect_line_number, "It does not match the instruction."))


def highlight_line(line_number, fade=-1): 
    text_widget.tag_add("highlight", f"{line_number}.0", f"{line_number}.end")
    if fade > 0:
        root.after(fade, remove_highlight)  # n秒後にハイライトを消す

def remove_highlight():
    text_widget.tag_remove("highlight", "1.0", tk.END)

def create_prompt():
    # ToDo: ユーザーの編集履歴も利用してコスト削減？
    user_code = text_widget.get("1.0", tk.END)

    # 必要な箇所だけ抜き出し
    _true_code = ""
    _user_code = ""
    for i, (row, user_row) in enumerate(zip(true_code.splitlines(), user_code.splitlines())):
        if i+1 in editable_lines:
            _true_code += f"{i+1}: {row}\n"
            _user_code += f"{i+1}: {user_row}\n"   

    # エラーログの抽出
    line_number = error_history[-1][0]
    error_message = error_history[-1][1]
    helps = "\n".join(next(iter([v['help'] for v in data.get('content', []) if v['line'] == line_number]), []))
    
    prompt = f"""\
インストラクションをよく理解し、正解のコードとユーザーのコードを比較した上で、ユーザーへのヒントを作成してください。
# インストラクション
{instruction}
# 正解のコード(全て)
{true_code}
# ユーザーのコード(一部抜粋)
{_user_code}
# 直前のエラー
line: {line_number}
error message: {error_message}
# 参考
{helps}
# 注意事項
小学生でも分かるようにヒントを考えてください。
ヒントは長くなりすぎないように一言(64字以内)にして下さい。
直接的な正解は教えず、そのヒントを示唆するように注意してください。
特にエラーが出ている箇所に着目してください。
構文的に違う書き方(while/while not)や、関数名、引数が異なる場合も不正解となるため、正解コードにたどり着くように助けてあげてください。
# 出力例
ヒント: インデントに気を付けて！
ヒント: whileの条件を見直してみて。
ヒント: 曲がる角度は角速度と時間から計算できるよ。計算してみてね！
"""
    return prompt
    
def show_hint():
    global hint_cool_time
    prompt = create_prompt()
    response = ask_chat_gpt(prompt)
    hint_label.config(text=response)
    hint_button.place_forget()
    hint_cool_time = 30
    
    # 一応ログを取っておく
    with open("log.txt", 'a') as f:
        f.write("@gpt-mini\n" + prompt + "\n" + response + "\n\n")


def reset_code():
    entry_widget.place_forget()
    update_code(default_code)


MAX_HINT_COUNT = 3
HINT_INTERVAL = 30

# グローバル変数
data = {}
instruction = ""
true_code = ""
default_code = ""
correct_answers = {}
editable_lines = []
line_number = 0
time_limit = 60
hinted_count = 0
last_hinted_time = 0
start_time = 0
timer_started = False
error_history = [(0, "なし")]

# メインウィンドウを作成
root = tk.Tk()
root.title("プログラミングクイズ")
root.state("zoomed")
root.resizable(False, False)

# インストラクション
instruction_text = tk.Text(root, width=64, height=12, font=("Meiryo", 12), wrap=tk.WORD, bg='#FFFAE6', fg='black', padx=10, pady=10)
instruction_text.place(x=20, y=64)
instruction_text.config(state=tk.DISABLED)  # 編集不可に設定

# プログラムコード用ウィジェット
text_widget = tk.Text(root, width=64, padx=24, border=0, font=("Meiryo", 12))
text_widget.place(x=780, y=64)

# タグ用のウィジェット
tag_widget = tk.Text(root, width=4, padx=8, pady=2, bg='white', fg='black', border=0, font=("Meiryo", 12))
tag_widget.tag_configure("right", justify="right")
tag_widget.place(x=720, y=64)
text_widget.config(state=tk.DISABLED)
text_widget.bind("<Button-1>", on_click)  # マウスクリックイベントをバインド

# Entryウィジェットを作成
entry_var = tk.StringVar()
entry_var.trace_add("write", on_entry_change)

entry_widget = tk.Entry(root, width=64, textvariable=entry_var, font=("Meiryo", 12), bg="lightgray")
entry_widget.place_forget()  # 初期状態では非表示
entry_widget.bind("<Return>", on_enter)
entry_widget.bind("<Tab>", on_tab)

# チェックボタンを作成
check_button = tk.Button(root, text="回答をチェック", command=check_answer, bg="#5E81AC", fg="white", font=("Meiryo", 12), relief=tk.FLAT, padx=15, pady=5)
check_button.place(x=720+480, y=720, anchor=tk.CENTER)

# リセットボタンを作成
reset_button = tk.Button(root, text="リセット", command=reset_code, bg="#5E81AC", fg="white", font=("Meiryo", 12), relief=tk.FLAT, padx=15, pady=5)
reset_button.place(x=720+240, y=720, anchor=tk.CENTER)

# 結果を表示するラベルを作成
result_label = tk.Label(root, text="", font=("Meiryo", 12))
result_label.place(x=720, y=960, anchor=tk.CENTER)

# エラーを表示するラベルを作成
error_label = tk.Label(root, text="", width=64, anchor=tk.W, font=("Meiryo", 12), wraplength=640, justify=tk.LEFT)
error_label.place(x=780, y=800)

# タイマー用プログレスバーを作成
progress_frame = tk.Frame(root)
progress_frame.pack(fill=tk.X)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(progress_frame, length=720, mode='determinate', variable=progress_var)
progress_bar.pack(padx=20, pady=10, fill=tk.X)

# ヒントボタンを作成
hint_button = tk.Button(root, text="ヒントを見る", command=show_hint, bg="#5E81AC", fg="white", font=("Meiryo", 12), relief=tk.FLAT, padx=15, pady=5)
hint_button.place_forget()

# ヒントを表示するラベルを作成
hint_label = tk.Label(root, text="", font=("Meiryo", 12), wraplength=640, justify=tk.LEFT, padx=10)
hint_label.place(x=20, y=480)


# 仮のクイズを読み込み
with open('./quiz/quiz_1-4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

update_quiz(data)

# メインループを開始
root.mainloop()