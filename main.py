#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from src.solution import Solution


if __name__ == '__main__':
    file_path = "data/test_data.csv"
    data = pd.read_csv(file_path)
    s = Solution()
    plan_table = s.cut(data)

    print(plan_table)
    plan_table.to_excel("data/生产计划表.xlsx", index=None, header=True)
