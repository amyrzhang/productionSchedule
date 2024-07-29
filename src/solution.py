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

        # 【计算每排方案】：如果尺寸数是3+，全组合放一排，如果尺寸数是1，n个放一排
        if len(products) == 1:
            rows = [min(6000 // products[0], orders[products[0]])]  # 排数
            mold_cnt: int = math.ceil(orders[products[0]] / rows[0])  # 生产模数
        elif len(products) == 2 and (6000 - sum(products) >= products[-1]):  # 两尺寸各方一个无法放满的情况
            rows = [1, 1]
            remaining = 6000 - sum(products)
            rows[0] += remaining // products[0]
            remaining -= products[0] * (remaining // products[0])
            rows[1] += remaining // products[1]
            mold_cnt = min(math.ceil(orders[products[0]] / rows[0]), math.ceil(orders[products[1]] / rows[1]))
        else:
            rows = [1] * len(products)
            mold_cnt = min([orders[size] for size in products])

        # 计算【生产模数】，取各产品订单数量的最小值
        cuts.append([products, rows, mold_cnt])

        # 更新订单表，把已出切割的产品去掉
        remaining_orders = {}
        for key, value in orders.items():
            if key in products:
                i = products.index(key)
                if value - rows[i] * mold_cnt <= 0:  # 若订单耗尽，删掉键
                    continue
                remaining_orders[key] = value - rows[i] * mold_cnt
            else:
                remaining_orders[key] = value
        orders = remaining_orders

    return cuts


def maximize_cutting(available_sizes, rope_length=6000):
    """
    全组合逻辑，寻找一排的全组合切割方案，要求 3+个尺寸
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


def process_aac_size(row):
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
        row['num'] = math.ceil(row['num'] / (1200 // length))  # 修改订单数量 num
        row['length'] = 1200
    else:
        row['length'] = length

    row['size1'], row['size2'], row['size3'] = length, width, 600
    return row


def is_by_product(width):
    """
    副产厚度，无副产返回 None
    :param width: 厚度
    :return: 副产厚度
    """
    if 1200 % width:  # 如果不能除尽
        return (1200 - (1200 // width) * width) // 100 * 100
    return None


class Solution:
    def __init__(self):
        # 订单表
        self.order_data = pd.DataFrame()

        # 砌块订单表
        self.aac_order_data = pd.DataFrame()

        # 生产计划表（输出表）
        self.plan_df = pd.DataFrame()

    def first_cut(self, data):
        """
        合并至【产品维度】，按长宽降序排列
        :param data: pd.DataFrame，订单表
        :return: pd.DataFrame
        """
        # 处理砌块
        df = data.apply(process_aac_size, axis=1)

        # 存储砌块原始订单数据映射表，筛选条件：类型为ALC，宽度符合
        self.aac_order_data = df[df['type'] == 'AAC']

        # 跨订单聚合到产品粒度
        grouped_df = df.groupby(['standards', 'length', 'size1', 'size2'])['num'].sum().reset_index()
        sorted_df = grouped_df.sort_values(by=['size2', 'size1', 'length'], ascending=False)

        # 计算【每排数量】和【总排数】
        sorted_df['每排数量'] = 1200 // sorted_df['size2']
        sorted_df['总排数'] = ceil(sorted_df['num'] / sorted_df['每排数量']).astype(int)

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
                for i, size in enumerate(row[0]):
                    if size == 1200:
                        while filtered_aac_dict:  # 遍历AAC订单，塞进去
                            type_value = 'AAC'
                            length, width, height = 600, filtered_aac_dict[0]['size1'], block_width
                            col_num = 1200 // width * row[1][i]  # 每排数量
                            filtered_aac_dict[0]['num'] -= row_num * row[1][i] * row[2]

                            if filtered_aac_dict[0]['num'] <= 0:
                                filtered_aac_dict.pop(0)
                    else:
                        type_value = 'ALC'
                        length, width, height = size, 600, block_width
                        col_num = row[1][i]

                    # 处理副产
                    if is_by_product(block_width):
                        by_product = str(length)+'*'+str(width)+'*'+str(is_by_product(block_width))
                        by_product_num = col_num * row[2]
                    else:
                        by_product, by_product_num = '', ''

                    cutting_patterns_dict = {
                        '序号': index, '产品类型': type_value,
                        '长': length, '宽': width, '高': height,
                        '每排数量': row_num, '排数': col_num, '生产模数': row[2],
                        '数量': row_num * col_num * row[2],
                        '外挂副产':by_product, '副产数量': by_product_num}  # 逐个取size

                    plan_patterns_list.append(cutting_patterns_dict)
        cutting_patterns_df = pd.DataFrame(plan_patterns_list)

        return cutting_patterns_df
