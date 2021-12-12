import os
import re
import csv
import toolbox as tb
import json

g_path = 'E:\\database\\BaiduIndex'  # 文件夹总路径
g_cache_path = 'E:\\database\\cache'
g_output_path = 'E:\\database\\output'


def extract_info(filename):  # str -> str | 从刚爬下来的文件名中提取信息
    info_list = re.split(r'[\[\],()]', filename)
    keyword = info_list[1]
    period = info_list[4]
    city_code = info_list[6].split('.')[0]
    return keyword, period, city_code


def classify_keyword(folder_path):  # path -> dict{合并后文件名: [将被合并的文件名]} | 对当前文件夹的关键词、时间进行提取唯一值，并分类。返回需要被合并的以及合并后文件的名称
    filename_list = os.listdir(folder_path)  # path -> list | 这里传入的path需要精确到存储csv文件的文件夹
    merged_dict = {}

    for filename in filename_list:
        keys = merged_dict.keys()
        keyword, period, city_code = extract_info(filename)

        target_name = keyword + ',' + period
        if target_name not in keys:
            merged_dict[target_name] = [filename]
        else:
            merged_dict[target_name].append(filename)
    tb.write_json(merged_dict)

    return merged_dict


def merge_files(folder_path):  # path -> csv | 把当前目录下面的所有csv合成一个，并放进指定文件夹
    merged_dict = classify_keyword(folder_path)
    keys = merged_dict.keys()

    for key in keys:  # 遍历每一个需要生成的文件
        filename_list = merged_dict[key]
        output = []

        keyword, period, city_code = extract_info(filename_list[0])  # 处理输出文件名
        output_name = f'{keyword},{period}'

        first_file = tb.read_csv(folder_path + '\\' + filename_list[0])  # 获取输出文件的时间列
        time_col = tb.transpose_matrix(first_file)[0]
        time_col[0] = 'Date'
        output.append(time_col)

        for filename in filename_list:
            keyword, period, city_code = extract_info(filename)
            file_path = folder_path + '\\' + filename
            data = tb.transpose_matrix(tb.read_csv(file_path))
            data[1][0] = city_code  # 用city_code替换原有的表头
            output.append(data[1])

        cache_path = f'{g_cache_path}\\{output_name}.csv'
        output = tb.transpose_matrix(output)
        tb.write_csv(output, cache_path)
        print(f'{output_name}已完成写入')


def generate_cache():  # 这一步是把原始数据合并一次，放进缓存文件夹
    # 由于百度爬下来的数据都是一年一个文件，所以只能先在这个基础上进行处理了
    years = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    words = ['word1', 'word2', 'word3', 'word4']
    for year in years:
        for word in words:
            g_sub_path = f'{g_path}\\{year}\\{word}'
            merge_files(g_sub_path)


def extract_info_cache(filename):  # str -> str | 从cache文件名提取信息
    info_list = re.split(r'[,至]', filename)
    keyword = info_list[0]
    start_date = info_list[1]
    end_date = info_list[2].split('.')[0]

    return keyword, start_date, end_date


def classify_keyword_cache(folder_path):  # path -> dict | 这里返回的字典键是最终输出文件名，值是所有需要用来合并的文件名
    filename_list = os.listdir(folder_path)  # path -> list | 这里传入的path需要精确到存储csv文件的文件夹
    keyword_dict = {}

    for filename in filename_list:
        keys = keyword_dict.keys()
        keyword, start_date, end_date = extract_info_cache(filename)
        year = int(start_date[0:4])
        if keyword not in keys:
            keyword_dict[keyword] = [year]
        else:
            keyword_dict[keyword].append(year)

    keywords = keyword_dict.keys()
    merged_dict = {}
    for keyword in keywords:
        max_year = max(keyword_dict[keyword])
        min_year = min(keyword_dict[keyword])
        merged_name = f'{keyword},{min_year}-01-01至{max_year}-12-31.csv'

        values = []
        for year in keyword_dict[keyword]:
            filename_to_merge = f'{keyword},{year}-01-01至{year}-12-31.csv'
            values.append(filename_to_merge)
        merged_dict[merged_name] = values

    return merged_dict


def merge_timeline(folder_path):
    merged_dict = classify_keyword_cache(folder_path)
    keys = merged_dict.keys()
    for key in keys:  # 进入处理每一个关键词的循环

        city_code_list = []
        for filename in merged_dict[key]:  # 先遍历所有子表把所有不重复的city_code取出来

            data = tb.transpose_matrix(tb.read_csv(folder_path + '\\' + filename))
            for col in data:
                city_code = col[0]
                if city_code != 'Date':
                    if city_code not in city_code_list:
                        city_code_list.append(city_code)

        output = [['Date']]  # 初始化表头
        for city_code in city_code_list:
            output.append([city_code])

        for filename in merged_dict[key]:  # 遍历所有子表把数据存入新大表
            data = tb.transpose_matrix(tb.read_csv(folder_path + '\\' + filename))

            empty_col = []  # 用来占位用的空数据
            for i in range(len(data[0]) - 1):
                empty_col.append('')
            data_dict = {}  # 把当前数据转为字典，方便查询
            for col in data:
                data_dict[col[0]] = col[1:]

            key_city = data_dict.keys()
            for col in output:
                if col[0] in key_city:
                    col += data_dict[col[0]]
                else:
                    col += empty_col

        output = tb.transpose_matrix(output)
        output_path = g_output_path + '\\' + key
        tb.write_csv(output, output_path)
        print(f'{key}')


if __name__ == '__main__':
    tb.create_path(g_cache_path)  # 创建输出目录
    tb.create_path(g_output_path)  # 创建输出目录

    merge_timeline(g_cache_path)



