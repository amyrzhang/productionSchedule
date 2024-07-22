#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from collections import defaultdict
from math import ceil


def adjust_row(row):
    """
    调整长宽高三列数据，使得结果为 长，宽，600
    板材：长，宽，600
    砌块：边，600，边
    :param row: pd.Series
    :return: pd.Series
    """
    filter_values = [x for x in row[['size1','size2','size3']] if x != 600]
    length, width = max(filter_values), min(filter_values)

    # 砌块尺寸单独处理，只把能被1200整除的边，定义为长边；如果长边不能被整除，交换位置
    if row['type'] == 'AAC' and 1200 % width:
        length, width = width, length

    row['size1'], row['size2'], row['size3'] = length, width, 600
    return row


def merge_and_sort(data):
    """
    合并至【产品维度】，按长宽降序排列
    :param data: pd.DataFrame
    :return: pd.DataFrame
    """
    grouped = data.groupby(['type','standards', 'size1', 'size2', 'size3']).sum('num').reset_index()
    grouped[['type','size1', 'size2', 'size3']] = grouped[['type','size1', 'size2', 'size3']].apply(adjust_row, axis=1)
    sorted = grouped.sort_values(by=['type','size2', 'size1', 'size3'], ascending=False)
    return sorted


class Solution:
    def __init__(self):
        # 新建生产计划表（输出表）
        self.columns = ['type', 'length', 'cuts', 'count', '宽', '高', '每模最大排数', '生产模数']
        self.plan_df = pd.DataFrame(columns=self.columns)

    def lengthwise_cut(self, df, width=1200):
        """
        纵切方案
        :param data: pd.DataFrame，订单数据，列名：规格，数量
        :return:
        """
        df = merge_and_sort(df)

        # 【逐宽处理】筛选出 size2 列等于 100 的子 DataFrame
        width_values = df['size2'].unique()

        # 新建生产计划表（输出表）
        columns = ['type', 'length', 'cuts', 'count', '宽', '高', '每模最大排数', '生产模数']
        plan_df = pd.DataFrame(columns=columns)

        for block_width in width_values:
            # block_width = 100
            row_num = width // block_width
            filtered_df = df[df['size2'] == block_width]

            # 【送去横切】将 size1 列作为索引，num 列作为值，生成 Series
            result_df = filtered_df[['type', 'size1', 'num']]
            result_df.columns = ['type', 'length', 'num']
            cutting_patterns = self.crosscut(result_df)

            # 输出DataFrame，补数据
            cutting_patterns['宽'] = block_width
            cutting_patterns['高'] = 600
            cutting_patterns['每模最大排数'] = row_num
            cutting_patterns['生产模数'] = cutting_patterns['count'].apply(lambda x: str(x//row_num)+"模"+str(x%row_num)+"排")
            columns = ['type', 'length', 'cuts', 'count', '宽', '高', '每模最大排数', '生产模数']
            cutting_patterns = cutting_patterns[columns]

            plan_df = pd.concat([plan_df, cutting_patterns], axis=0)

        return plan_df

    def crosscut(self, df, rope_length=6000):
        """
        子问题：考虑纵切完成，产出n个长度为【6000】的【子胚体】，则子问题是一维切割问题
        预处理：把6个【200】的砌块，当成1个【1200】的板材，那么板材和砌块可以放在一起计算
        TODO: 没有尺寸1200的板材吧？--> 有的，不好说
        :param orders: pd.Series，其中index为长度，values为数量
        :return: 生产计划表，pd.DataFrame
        """
        # 筛选AAC小绳子的订单
        small_rope_df = df[(df['type'] == 'AAC') & (df['length'] == 200)]
        other_df = df[~((df['type'] == 'AAC') & (df['length'] == 200))]

        # 计算AAC小绳子的总数量
        total_small_ropes = small_rope_df['num'].sum()

        # 计算每次切割可以产生的1200单位
        units_per_cut = rope_length // 1200
        small_rope_units = total_small_ropes // 6
        remaining_small_ropes = total_small_ropes % 6

        cutting_plans = []

        # 添加完整的1200长度的订单
        if small_rope_units > 0:
            cutting_plan = {
                'type': 'AAC',
                'length': 1200,
                'cuts': [200] * 6,
                'count': small_rope_units
            }
            cutting_plans.append(cutting_plan)

        # 如果有剩余的小绳子，记录下来
        if remaining_small_ropes > 0:
            cutting_plan = {
                'type': 'AAC',
                'length': remaining_small_ropes * 200,
                'cuts': [200] * remaining_small_ropes,
                'count': 1
            }
            cutting_plans.append(cutting_plan)

        # 处理其他订单
        for _, row in other_df.iterrows():
            cutting_plan = {
                'type': row['type'],
                'length': row['length'],
                'cuts': [row['length']],
                'count': row['num']
            }
            cutting_plans.append(cutting_plan)

        return pd.DataFrame(cutting_plans)
