#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from collections import defaultdict
from numpy import ceil


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


def first_cut(data):
    """
    合并至【产品维度】，按长宽降序排列
    :param data: pd.DataFrame，订单表
    :return: pd.DataFrame
    """
    grouped = data.groupby(['type','standards', 'size1', 'size2', 'size3']).sum('num').reset_index()
    grouped[['type','size1', 'size2', 'size3']] = grouped[['type','size1', 'size2', 'size3']].apply(adjust_row, axis=1)
    sorted = grouped.sort_values(by=['type','size2', 'size1', 'size3'], ascending=False)

    # 处理砌块
    sorted['length'] = sorted.apply(lambda row: row['size1'] if row['type'] == 'ALC' else 1200, axis=1)

    # 计算【每排数量】和【总排数】
    sorted['每排数量'] = 1200 // sorted['size2']
    sorted['总排数'] = ceil(sorted['num'] // sorted['每排数量']).astype(int)

    return sorted


class Solution:
    def __init__(self):
        # 新建生产计划表（输出表）
        self.columns = ['type', 'length', 'cuts', 'count', '宽', '高', '每模最大排数', '生产模数']
        self.plan_df = pd.DataFrame(columns=self.columns)

    def cut(self, df, width=1200):
        """
        处理数据流和两次切割
        :param data: pd.DataFrame，订单数据，列名：规格，数量
        :return:
        """
        df = first_cut(df)

        # 宽度列表
        width_values = df['size2'].unique()

        # 新建生产计划表（输出表）
        columns = ['type', 'length', 'cuts', 'count', '宽', '高', '排数', '生产模数']
        plan_df = pd.DataFrame(columns=columns)

        # 【逐宽处理】
        for block_width in width_values:
            block_width = 100
            row_num = width // block_width
            filtered_df = df[df['size2'] == block_width]

            # 【送去横切】将 size1 列作为索引，num 列作为值，生成 Series
            result_df = filtered_df
            cutting_patterns = self.second_cut(result_df)

            # 输出DataFrame，补数据
            cutting_patterns['宽'] = block_width
            cutting_patterns['高'] = 600
            cutting_patterns['排数'] = row_num
            cutting_patterns['生产模数'] = cutting_patterns['count'].apply(lambda x: str(x//row_num)+"模"+str(x%row_num)+"排")
            columns = ['type', 'length', 'cuts', 'count', '宽', '高', '排数', '生产模数']
            cutting_patterns = cutting_patterns[columns]

            plan_df = pd.concat([plan_df, cutting_patterns], axis=0)

        return plan_df

    def second_cut(self, order, mold_length=6000):
        """
        子问题：考虑纵切完成，产出n个长度为【6000】的【子胚体】，则子问题是一维切割问题
        预处理：把6个【200】的砌块，当成1个【1200】的板材，那么板材和砌块可以放在一起计算
        TODO: 没有尺寸1200的板材吧？--> 有的，不好说
        :param orders: pd.DataFrame
        :return: 生产计划表，pd.DataFrame
        """
        cuts = []
        for size, count in order:
            while mold_length >= size and count > 0:
                cuts.append(size)
                mold_length -= size
                count -= 1
        df['cuts'], df['remaining'] = zip(*df['length'].apply(lambda x: cut_rope(x, [(2720, 5), (1500, 5), (1200, 5)])))

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
