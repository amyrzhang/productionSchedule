#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from numpy import ceil
import math


def second_cut(orders):
    """
    计算切割方案，每排数量，生产模数
    :param orders: dict，订单信息，键是长度，值是订单数量
    :return: list[list]，子列表依次为 尺寸列表，每排数量，生产模数
    """
    cuts = []

    while orders:
        products = maximize_cutting(list(orders.keys()))

        # 【计算每排方案】：如果尺寸数是2+，全组合放一排，如果尺寸数是1，n个放一排
        if len(products) == 1:
            rows = min(6000 // products[0], orders[products[0]])  # 排数
            mold_cnt = math.ceil(orders[products[0]] / rows)  # 生产模数
        else:
            rows = 1
            mold_cnt = min([orders[size] for size in products])

        # 计算【生产模数】，取各产品订单数量的最小值
        cuts.append([products, rows, mold_cnt])

        # 更新订单表
        remaining_orders = {}
        for key, value in orders.items():
            if key in products:
                if value - rows * mold_cnt <= 0:  # 若订单耗尽，删掉键
                    continue
                remaining_orders[key] = value - rows * mold_cnt
            else:
                remaining_orders[key] = value
        orders = remaining_orders

    return cuts


def maximize_cutting(available_sizes, rope_length=6000):
    """
    全组合逻辑，寻找一排的全组合切割方案，要求至少有 两个尺寸
    :param available_sizes: list，订单产品列表
    :param rope_length: int，胚体长度6000
    :return: list，单模切割方案，对应生产计划表的多行
    """
    products = []
    used_sizes = set()

    for size in sorted(available_sizes, reverse=True):  # 从大到小排序
        if size <= rope_length and size not in used_sizes:
            products.append(size)
            used_sizes.add(size)
            rope_length -= size

        if rope_length == 0:
            break
    return products


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
    grouped_df = data.groupby(['type','standards', 'size1', 'size2', 'size3']).sum('num').reset_index()
    grouped_df[['type','size1', 'size2', 'size3']] = grouped_df[['type','size1', 'size2', 'size3']].apply(adjust_row, axis=1)
    sorted_df = grouped_df.sort_values(by=['type','size2', 'size1', 'size3'], ascending=False)

    # 处理砌块
    sorted_df['length'] = sorted_df.apply(lambda row: row['size1'] if row['type'] == 'ALC' else 1200, axis=1)

    # 计算【每排数量】和【总排数】
    sorted_df['每排数量'] = 1200 // sorted_df['size2']
    sorted_df['总排数'] = ceil(sorted_df['num'] // sorted_df['每排数量']).astype(int)

    return sorted_df


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
        plan_patterns_list = []
        for block_width in width_values:
            # block_width = 100
            row_num = width // block_width
            filtered_df = df[df['size2'] == block_width]

            # 【送去横切】将 size1 列作为索引，num 列作为值，生成 Series
            result_dict = dict(zip(filtered_df['length'], filtered_df['总排数']))
            cutting_patterns = second_cut(result_dict)
            # df = pd.DataFrame(cutting_patterns, columns=['sizes', '排数', '生产模数'])

            # 输出DataFrame，补数据
            for index, row in enumerate(cutting_patterns):
                for size in row[0]:
                    cutting_patterns_dict = {}# 逐个取size
                    cutting_patterns_dict['序号'] = index
                    cutting_patterns_dict['长'] = size
                    cutting_patterns_dict['宽'] = block_width
                    cutting_patterns_dict['高'] = 600
                    cutting_patterns_dict['每排数量'] = row_num
                    cutting_patterns_dict['排数'] = row[1]
                    cutting_patterns_dict['生产模数'] = row[2]
                    cutting_patterns_dict['数量'] = row_num * row[1] * row[2]
                    plan_patterns_list.append(cutting_patterns_dict)
        cutting_patterns_df = pd.DataFrame(plan_patterns_list)

        return cutting_patterns_df


