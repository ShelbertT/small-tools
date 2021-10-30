import sys
import pandas as pd
import math
import numpy as np
import os
import time


def mkdir(path):
    path = path.strip()
    path = path.rstrip("\\")
    exist = os.path.exists(path)
    if not exist:
        os.makedirs(path)
    else:
        return


def get_repetition(sheet):  # 根据repetition值重新生成一个issue sheet
    sheet.set_index("Name", inplace=True)
    result = pd.DataFrame()
    for i in range(len(sheet["Repetition"])):
        repetition = sheet["Repetition"][i]
        for j in range(repetition):
            result = result.append(sheet.iloc[i:i + 1])
    result.reset_index(inplace=True)
    return result


def get_unassigned(sheet):  # 把已经assign出去的给删掉，只保留没有assign的，并且重置index
    result = pd.DataFrame()
    for i in range(len(sheet.index)):
        if not sheet["Assigned"][i]:
            result = result.append((sheet.iloc[i:i + 1]))
    result.reset_index(inplace=True)
    return result


def get_average_workload(original=False):  # 计算Expected_Workload为空的每个人平均应有的工作量，默认使用未分配的表格来计算
    if not original:
        humans_temp = get_unassigned(humans)
        issues_temp = get_unassigned(issues)
    else:
        humans_temp = humans
        issues_temp = issues
    customized_workload = 0
    customized_human = 0

    for i in range(len(humans_temp.index)):
        if not pd.isnull(humans_temp["Expected_Workload"][i]):
            customized_workload += humans_temp["Expected_Workload"][i]  # 自定义的总量
            customized_human += 1  # 自定义的人数
        else:
            continue

    workload = 0
    for i in range(len(issues_temp.index)):
        workload += issues_temp["Workload"][i]
    up = workload - customized_workload
    down = len(humans_temp.index) - customized_human
    if down == 0:
        return 0

    return math.ceil(up/down)


def rearrange_sheet(sheet):  # 把sheet全部打乱重排序
    length = len(sheet.index)
    random_list = np.random.permutation(length)
    sheet.set_index("Name", inplace=True)
    result = pd.DataFrame()
    for i in range(length):
        j = random_list[i]
        result = result.append(sheet.iloc[j:j + 1])
    result.reset_index(inplace=True)
    return result


def distribute_workload(sheet1, sheet2):  # sheet1是人类，sheet2是测试内容
    human_workload = {}
    issue_index_temp = 0
    for i in range(len(sheet1.index)):  # 遍历所有人类
        workload_list = pd.DataFrame()
        workload_sum_temp = 0
        while workload_sum_temp < average_workload:
            workload_list = workload_list.append(sheet2.iloc[issue_index:issue_index + 1])
            if issue_index < len(sheet2.index) - 1:
                issue_index_temp += 1
                workload_sum_temp += sheet2["Workload"][issue_index]
            else:
                break
        print('当前任务工作总量为' + str(workload_sum))
        print(workload_list)


def check_qualify(issue, human):
    condition1 = False
    condition2 = False
    condition3 = False
    condition4 = False
    condition5 = False
    if issues["Dev_Excluded"][issue] != humans["Name"][human]:
        condition1 = True
    if issues["PE_Excluded"][issue] != humans["Name"][human]:
        condition2 = True
    if workload_sum + issues["Workload"][issue] <= Expected_Workload:
        condition3 = True
    if issues["ID"][issue] not in work_id_list:
        condition4 = True
    if not issues["Assigned"][issue]:
        condition5 = True

    if condition1 and condition2 and condition3 and condition4 and condition5:
        # 这里一共判定五个条件：不是相关dev、不是相关PE、总工作量不超过期望值、这人此前没有同一个issue、该issue此前没有被assign
        return True
    else:
        return False


def check_all_assign(sheet, sheet_name):  # 检查当前sheet的assign状态
    all_assign = True
    false_number = 0
    for i in range(len(sheet.index)):
        if not sheet["Assigned"][i]:
            all_assign = False
            false_number += 1
    # print(f'{false_number} unit(s) in the sheet [{sheet_name}] have not been assigned.')
    return all_assign


def generate_single_text(id_temp, data):  # 格式化单个人物的文本
    current_line = humans.loc[humans['ID'] == id_temp]
    current_line.reset_index(inplace=True)  # 前面一句话是用一个参数存储当前行，所以这里才需要重置其索引方便我们获取
    human_name = current_line["Name"][0]
    # 这几行是为了找出当前id所对应的真名

    result = ['---\n',
              f'## {title} for {human_name}\n\n',
              f'- @{id_temp}, Here are your assigned issues.\n',
              f'- Test Resource: `{resource}`\n',
              '### Test Cases and the PoCs you should go to when issues are detected:\n']
    workload_sum_temp = 0
    for i in range(len(data.index)):
        test_name = data["Name"][i]
        test_id = data["ID"][i]
        test_workload = data["Workload"][i]
        test_link = f'https://devtopia.esri.com/runtime/{repo}/issues/{test_id}'
        line1 = f'- [ ] [{test_name}]({test_link}) Workload: **{test_workload}**-----'
        workload_sum_temp += test_workload
        result.append(line1)

        current_test_line = issues.loc[issues['ID'] == data['ID'][i]]
        current_test_line.reset_index(inplace=True)
        dev_excluded = current_test_line["Dev_Excluded"][0]
        pe_excluded = current_test_line["PE_Excluded"][0]
        line2 = f'Dev: **{dev_excluded}**, PE: **{pe_excluded}**\n'
        result.append(line2)

    line = f'- Your overall workload is: **{workload_sum_temp}**, you have **{estimate}** day(s) to finish them. ' \
           f'Thank you for your contribution.\n\n\n\n\n'
    result.append(line)
    return result


if __name__ == '__main__':
    passcode = False
    at_least_one_valid = False
    restart_count = 0  # 这个参数用来计算程序重启的次数
    restart_limit = 100  # 限制程序重启的次数
    best_rating = 100
    print('---Designed and Created by Haorui Su---')
    with pd.ExcelFile("Info.xlsx") as xls:
        mode = pd.read_excel(xls, "mode")
    resource = mode["Resource"][0]
    title = mode["Title"][0]
    repo = mode["Repo"][0]
    estimate = mode["Estimate"][0]
    optimal_solution = int(mode["Optimal_Solution"][0])
    if optimal_solution == 0:  # 判断输入值是否为布尔值，如果不是，则更新restart_limit，提供个性化重复次数
        optimal_solution = False
    elif optimal_solution == 1:
        optimal_solution = True
    else:
        restart_limit = optimal_solution

    while not passcode and restart_count < restart_limit:  # 初始化分配，不满足条件就不会退出循环，除非超出重试次数
        empty_assignment = False
        valid = False
        # passcode为False且count<limit时才会反复进行。如果optimal_solution不为True，则在首次随机出满足条件的东西时就会退出循环，否则会一直循环至restart_limit取最优解
        restart_count += 1
        print(f'\nStart trying to assign issue for the {restart_count} time, program will restart itself if result cannot meet demand.')
        with pd.ExcelFile("Info.xlsx") as xls:
            humans = pd.read_excel(xls, "humans")
            issues = pd.read_excel(xls, "issues")
        issues = get_repetition(issues)
        humans = rearrange_sheet(humans)
        issues = rearrange_sheet(issues)
        # 上面这些都是初始化内容用的，把需要的东西读进内存

        entire_dict = {}
        issues["Assigned"] = False
        humans["Assigned"] = False
        rating = 0  # 给当前分配的结果打分，打分机制是考虑进Expected_Workload后的标准差
        rating_workload = get_average_workload()  # 这个是针对未被个性化的人的打分标准

        for human_index in range(len(humans.index)):  # 开始给每个人分配工作
            average_workload = get_average_workload()  # 分配工作量时会在每分配完一个人就重新计算工作总量，但打分时不会这样，打分使用的是一开始的期望
            if average_workload == 0:
                break
            if not pd.isnull(humans["Expected_Workload"][human_index]):  # 如果被指定了工作量，则使用指定的值。pd.isnull是对空置的判断
                Expected_Workload = humans["Expected_Workload"][human_index]
                rating_workload = Expected_Workload
            else:
                Expected_Workload = average_workload

            human_id = humans["ID"][human_index]
            workload_sum = 0  # 初始化这个人的总工作量
            work_id_list = []  # 记录他手中的issue ID

            issue_index = 0
            human_job = pd.DataFrame()  # 这个dataframe用来存储当前这个人的任务

            while workload_sum < Expected_Workload and issue_index < len(issues.index):  # 给当前人类分配工作
                qualify = check_qualify(issue_index, human_index)  # 总工作量不超过期望值
                if qualify:
                    work_id_list.append(issues["ID"][issue_index])
                    workload_sum += issues["Workload"][issue_index]
                    issues.at[[issue_index], ["Assigned"]] = True  # 这里会把issues初始dataframe的东西给改成True

                    human_job = human_job.append(issues.iloc[issue_index:issue_index+1])
                issue_index += 1

            rating = math.pow((rating_workload - workload_sum), 2) + rating  # 差值的平方加入rating
            humans.at[[human_index], ["Assigned"]] = True  # 这里会把humans初始dataframe的东西给改成True
            try:
                human_job.set_index("Name", inplace=True)
            except:
                empty_assignment = True
                break
            human_job.reset_index(inplace=True)  # 这两句是为了抹掉原有的index
            entire_dict[human_id] = human_job

        if empty_assignment:
            continue

        humans_all_assigned = check_all_assign(humans, 'humans')
        issues_all_assigned = check_all_assign(issues, 'issues')
        if humans_all_assigned and issues_all_assigned and average_workload != 0:
            valid = True  # 判断当前结果的有效性  # average_workload是从上一个for循环得到的参数，如果它等于0，说明这次随机的有问题，就重新执行随机
            at_least_one_valid = True
        if not valid:
            continue  # 如果无效，会直接重新刷新，不会进行下面的打分

        rating = math.sqrt(rating/len(humans.index))  # 当前结果的打分
        print(f'Rating: {rating}')
        if rating < best_rating:
            best_rating = rating  # 记录当前最好的分数
            best_entire_dict = entire_dict  # 把当前最好的dict存下来
            print(f'The best current rating is {best_rating}.')

        if humans_all_assigned and issues_all_assigned and not optimal_solution:  # 如果不需要最优解，则在第一个可行解就会直接退出循环
            passcode = True
    # 上面的内容是为了以防当前分配不满足所有条件，会重新进行随机分配

    if not at_least_one_valid:
        print('[WARNING] Restart exceeds limit, your request cannot be fulfilled, please change your info settings.')
        sys.exit(0)

    print('\nSuccessfully assigned all Humans and Issues, initiating writing.')
    ultimate_list = []
    for keys in dict.keys(best_entire_dict):
        single_text = generate_single_text(keys, best_entire_dict[keys])
        ultimate_list += single_text

    with open("report.txt", 'w', encoding='utf-8') as f:
        f.writelines(ultimate_list)
    print(f'All results have been written into report.txt, the rating of this distribution is: {best_rating}'
          f'\nProgram will automatically close in 10s.')
    time.sleep(10)
