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


class Solution:
    def __init__(self):
        # 订单表
        self.order_data = pd.DataFrame()

        # 砌块订单表
        self.aac_order_data = pd.DataFrame()

        # 生产计划表（输出表）
        self.plan_df = pd.DataFrame()

    def process_aac_size(self,row):
        """
        【处理砌块逻辑】调整长宽高三列数据，增加一列length，使得结果为 长，宽，600
        板材：长，600，宽
        砌块：600，长，宽
        :param row: pd.Series
        :return: pd.Series
        """
        filter_values = [x for x in row[['size1', 'size2', 'size3']] if x != 600]
        length, width = max(filter_values), min(filter_values)

        # 砌块尺寸单独处理，只把能被1200整除的边，定义为长边；
        if row['type'] == 'AAC':
            if 1200 % length:  # 如果长边不能被整除，交换位置
                length, width = width, length
            # row['num'] = math.ceil(row['num'] / (1200 // length))  # 修改订单数量 num
            row['length'] = 1200
        else:
            row['length'] = length

        row['size1'], row['size2'], row['size3'] = length, width, 600
        return row

    def first_cut(self,data):
        """
        合并至【产品维度】，按长宽降序排列
        :param data: pd.DataFrame，订单表
        :return: pd.DataFrame
        """
        # 处理砌块
        df = data.apply(self.process_aac_size, axis=1)

        # 存储砌块原始订单数据映射表，筛选条件：类型为ALC，宽度符合
        self.aac_order_data = df[df['type'] == 'AAC']

        # 跨订单聚合到产品粒度
        grouped_df = df.groupby(['standards', 'length', 'size2'])['num'].sum().reset_index()
        sorted_df = grouped_df.sort_values(by=['size2', 'length'], ascending=False)

        # 计算【每排数量】和【总排数】
        sorted_df['每排数量'] = 1200 // sorted_df['size2']
        sorted_df['总排数'] = ceil(sorted_df['num'] // sorted_df['每排数量']).astype(int)

        return sorted_df

    def cut(self, data):
        """
        处理数据流和两次切割
        :param data: pd.DataFrame，订单数据，列名：规格，数量（无规格，无产品类型）
        :return:
        """
        self.order_data = data
        df = self.first_cut(data)

        # 宽度列表
        width_values = df['size2'].unique()

        # 【逐宽处理】
        plan_patterns_list = []
        for block_width in width_values:
            # block_width = 100
            row_num = 1200 // block_width
            filtered_df = df[df['size2'] == block_width]

            # 砌块订单映射表
            filtered_aac_df = self.aac_order_data[self.aac_order_data['size2'] == block_width]
            filtered_aac_dict = filtered_aac_df[['size1', 'num']].to_dict('records')

            # 【送去横切】将 size1 列作为索引，num 列作为值，生成 Series
            result_dict = dict(zip(filtered_df['length'], filtered_df['总排数']))
            cutting_patterns = second_cut(result_dict)

            # 输出DataFrame，补数据
            for index, row in enumerate(cutting_patterns):
                for size in row[0]:
                    if size == 1200:
                        # 遍历AAC订单，塞进去
                        while filtered_aac_dict:
                            type_value = 'AAC'
                            length = filtered_aac_dict[0]['size1']
                            cut_num = 1200//length
                            col_num = cut_num * row[1]
                            num = row_num * col_num * row[2]
                            filtered_aac_dict[0]['num'] -= num
                    else:
                        type_value, length, col_num = 'ALC', size, row[1]
                    cutting_patterns_dict = {}  # 逐个取size
                    cutting_patterns_dict['序号'] = index
                    cutting_patterns_dict['长'] = size
                    cutting_patterns_dict['宽'] = 600
                    cutting_patterns_dict['高'] = block_width
                    cutting_patterns_dict['每排数量'] = row_num
                    cutting_patterns_dict['排数'] = row[1]
                    cutting_patterns_dict['生产模数'] = row[2]
                    cutting_patterns_dict['数量'] = row_num * row[1] * row[2]
                    plan_patterns_list.append(cutting_patterns_dict)
        cutting_patterns_df = pd.DataFrame(plan_patterns_list)

        return cutting_patterns_df
