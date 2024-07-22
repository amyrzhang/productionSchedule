#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from src.transfer import reader
from src.solution import Solution
from solution import merge_and_sort

if __name__ == '__main__':
    file_path = "data/test_data.csv"

    data = pd.read_csv(file_path)
    s = Solution()
    plan_table = s.lengthwise_cut(data)

    print(plan_table)
    plan_table.to_csv("../data/production_plan.csv", index=False, encoding='gbk')
