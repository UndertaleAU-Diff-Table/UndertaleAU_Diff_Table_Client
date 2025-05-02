import pandas as pd

from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

import shutil

import git

import atexit

import sys

import fnmatch

#table_list = pd.read_csv("./list.csv")


#ログ表示用


def logText(log_text):

    print("[log] " + str(log_text))


#難易度表のディレクトリー名用


#Table Directory Formatの略


def tdf(table_name, table_auther):

    return "[" + table_auther + "] " + table_name


#難易度表アップデート用

def tableUpdate(table_list):
    #if isUpdate:
    #    return
    #isUpdate = 1


    #log_text(str(table_list.shape[0]) + "行存在")


    for i in range(table_list.shape[0]):

        print(tdf(table_list.iloc[i, 0], table_list.iloc[i, 1]))

        if os.path.isdir("./[" + table_list.iloc[i, 1] + "] " + table_list.iloc[i, 0]) == False:

            git.Repo.clone_from("https://github.com/" + table_list.iloc[i, 1] + "/" + table_list.iloc[i,0] + ".git", tdf(table_list.iloc[i, 0], table_list.iloc[i, 1]))

            logText("Clone")

        else:

            repo = git.Repo("./" + tdf(table_list.iloc[i, 0], table_list.iloc[i, 1]))

            origin = repo.remotes.origin

            origin.pull()

            logText("Pull")


class DiffTableClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UndertaleAU Diff Table Client")
        self.resizable(True, True)
        self.geometry("1280x720")

        self.data = None
        self.current_table = None
        self.current_table_index = None
        self.diff_data = None
        self.cleared = {}

        self.load_cleared_status()
        self.create_widgets()
        self.update_tables()

    def create_widgets(self):
        # 上部操作ボタン
        frame_top = ttk.Frame(self)
        frame_top.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(frame_top, text="Update", command=self.update_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Exit", command=self.quit).pack(side=tk.LEFT, padx=5)

        # 左側: 難易度表一覧
        self.table_listbox = tk.Listbox(self)
        self.table_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.table_listbox.bind("<<ListboxSelect>>", self.on_table_select)

        # 中央: 難易度一覧
        self.difficulty_listbox = tk.Listbox(self)
        self.difficulty_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.difficulty_listbox.bind("<<ListboxSelect>>", self.on_difficulty_select)

        # 右側: 詳細表示
        self.tree = ttk.Treeview(self, columns=["Cleared", "AU", "Auther", "Detail"], show="headings")
        self.tree.heading("Cleared", text="✓")
        self.tree.heading("AU", text="AU")
        self.tree.heading("Auther", text="Auther")
        self.tree.heading("Detail", text="Detail")
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        item = self.tree.item(item_id)
        values = item["values"]
        if not values:
            return

        name = self.table_list.iloc[self.current_table_index, 0]
        author = self.table_list.iloc[self.current_table_index, 1]

        key = (values[1], values[2], values[3])
        current = self.cleared.get(key, False)
        self.cleared[key] = not current
        self.save_cleared_status()

        # 更新表示
        self.on_difficulty_select(None)


    def update_tables(self):
        try:
            self.data = pd.read_csv("./list.csv")
            tableUpdate(self.data)
            self.table_list = self.data
            self.table_listbox.delete(0, tk.END)
            for i in range(self.table_list.shape[0]):
                self.table_listbox.insert(tk.END, tdf(self.table_list.iloc[i, 0], self.table_list.iloc[i, 1]))
        except Exception as e:
            messagebox.showerror("アップデート失敗", str(e))

    def load_cleared_status(self):
        self.cleared = {}
        if os.path.exists("save.csv"):
            df = pd.read_csv("save.csv")
            for _, row in df.iterrows():
                try:
                    key = (
                        str(row["AU"]).strip(),
                        str(row["Auther"]).strip(),
                        str(row["Detail"]).strip()
                    )
                    self.cleared[key] = str(row["cleared"]).lower() == "true"
                except Exception as e:
                    print(f"[load_cleared_status error] {e}")

    def save_cleared_status(self):
        rows = []
        for key, cleared in self.cleared.items():
            au, auther, detail = key
            rows.append({"AU": au, "Auther": auther, "Detail": detail, "cleared": cleared})
        df = pd.DataFrame(rows)
        df.to_csv("save.csv", index=False)

    def show_list_in_console(self):
        if self.data is not None:
            viewList(self.data)

    def on_table_select(self, event):
        selection = self.table_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.current_table_index = index

        name = self.table_list.iloc[index, 0]
        author = self.table_list.iloc[index, 1]
        base_path = f"./[{author}] {name}"

        try:
            table_csv = pd.read_csv(f"{base_path}/data.csv")
            self.current_table = table_csv
            self.difficulty_listbox.delete(0, tk.END)
            for level in range(table_csv.iloc[0, 1], table_csv.iloc[0, 2] + 1):
                level_path = f"{base_path}/{level}.csv"
                if os.path.exists(level_path):
                    level_data = pd.read_csv(level_path)
                    self.difficulty_listbox.insert(tk.END, f"{level} ({len(level_data)})")
                else:
                    self.difficulty_listbox.insert(tk.END, f"{level} (0)")
        except Exception as e:
            messagebox.showerror("読み込み失敗", str(e))

    def on_difficulty_select(self, event):
        selection = self.difficulty_listbox.curselection()
        if not selection or self.current_table is None:
            return
        diff_level = self.difficulty_listbox.get(selection[0]).split()[0]

        name = self.table_list.iloc[self.current_table_index, 0]
        author = self.table_list.iloc[self.current_table_index, 1]
        path = f"./[{author}] {name}/{diff_level}.csv"

        try:
            self.diff_data = pd.read_csv(path)
            self.tree.delete(*self.tree.get_children())
            for i in range(self.diff_data.shape[0]):
                au = self.diff_data.iloc[i, 0]
                auther = self.diff_data.iloc[i, 1]
                detail = self.diff_data.iloc[i, 2]
                key = (au, auther, detail)
                checked = self.cleared.get(key, False)
                check_symbol = "✔" if checked else "✘"
                self.tree.insert("", tk.END, values=[
                    check_symbol,
                    au,
                    auther,
                    detail
                ])
        except Exception as e:
            messagebox.showerror("難易度データ読み込み失敗", str(e))


#main関数

#それ以上でもそれ以下でもない


def main():

    print("UndertaleAU Diff Table Client ver 0.02")

    window = DiffTableClient()
    window.mainloop()

    #question()


#main関数を実行してるだけ


if __name__ == "__main__":
    main()