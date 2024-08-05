#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
from src.solution import Solution


# 对上传后的文件进行处理
def process_excel(file_path):
    try:
        # 对文件的处理可根据个人需求自行编写，下面这段为我对表格里的某一列数据进行处理，并将处理后的这列数据单独保存为xls格式的文件。
        # 通过上传的文件名打开Excel文件
        column_names = ['type','standards','size1','size2','size3','num']
        workbook = pd.read_excel(file_path, engine='openpyxl',skiprows=0,names=column_names)

        # 文件处理
        s = Solution()
        plan_table = s.cut(workbook)

        # 保存处理后的文件
        if os.access("./processed_file.xlsx", os.F_OK):
            os.remove("./processed_file.xlsx")
        plan_table.to_excel('./processed_file.xlsx', index=False, header=True)
        # 文件处理成功则返回True
        return True
    except Exception as e:
        print(f"处理文件时出现错误: {str(e)}")
        return False


def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
    if file_path:
        result = process_excel(file_path)
        if result is True:
            result_label.config(text="处理成功")
            save_button.config(state=tk.NORMAL)
        else:
            result_label.config(text="处理失败")


def save_processed_file():
    save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
    if save_path:
        # 将处理后的文件保存到用户选择的位置
        import shutil
        shutil.copy("processed_file.xlsx", save_path)
    # 保存成功后自动关闭窗口
    root.destroy()


if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()
    root.geometry('400x300')
    root.title("墙板切割计划排程工具")

    # 创建说明文字
    comment_text = """
        \n\n\n说明：请上传xlsx格式文件，示例如下：
        列名分别为：产品类型，技术标准，长，宽，高，数量        
    """
    comment_label = tk.Label(root, text=comment_text,fg="red")
    comment_label.pack()

    # # 创建示例数据
    # comment_img = tk.PhotoImage(file="demo.png")
    # label_img = tk.Label(root, image=comment_img)
    # label_img.pack()

    # 创建上传按钮
    upload_button = tk.Button(root, text="上传Excel文件", command=upload_file, width=10, height=2)
    upload_button.pack()

    # 创建处理结果标签
    result_label = tk.Label(root, text="")
    result_label.pack()

    # 创建保存按钮（初始状态禁用）
    save_button = tk.Button(root, text="保存处理后的文件", command=save_processed_file, state=tk.DISABLED, width=30,
                            height=2)
    save_button.pack()

    # 启动主循环
    root.mainloop()


# if __name__ == '__main__':
#     file_path = "data/test_data.csv"
#     data = pd.read_csv(file_path)
#
#
#     s = Solution()
#     plan_table = s.cut(data)
#
#     print(plan_table)
#     plan_table.to_excel("data/生产计划表.xlsx", index=None, header=True)
