import json
import pandas as pd
import requests
import datetime
import sys
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import time

# 读取配置文件
CONFIG_FILE = './Info.json'
f = open(CONFIG_FILE, "r", encoding='utf-8')
Info = json.load(f)
print(Info)


# word_url = 'http://index.baidu.com/api/SearchApi/thumbnail?area=0&word={}'

# 配置chrome，设置端口
# chrome_options = Options()
# chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9232")
# chrome_driver = "E:\\Python\\chromedriver.exe"
# driver = webdriver.Chrome(chrome_driver, chrome_options=chrome_options)

def decrypt(t, e):
    try:
        n = list(t)
    except:
        print(t, e)
        sys.exit(0)
    i = list(e)

    a = {}
    result = []
    ln = int(len(n) / 2)

    start = n[ln:]
    end = n[:ln]

    for j, k in zip(start, end):
        a.update({k: j})

    for j in e:
        result.append(a.get(j))

    return ''.join(result)


# 获取unique ID
def get_ptbk(uniqid):
    url = f'http://index.baidu.com/Interface/ptbk?uniqid={uniqid}'
    ptbk_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Cookie': COOKIES,
        'DNT': '1',
        'Host': 'index.baidu.com',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://index.baidu.com/v2/main/index.html',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/75.0.3770.90 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    while True:
        try:
            resp = requests.get(url, headers=ptbk_headers)
            while resp.text.strip() == '':
                print('获取页面为空')
                resp = requests.get(url, timeout=10)

            while resp.status_code != 200:
                print('获取uniqid失败')
                resp = requests.get(url, timeout=10)

            ptbk0 = resp.json()
            ptbk = ptbk0.get('data')

            return ptbk
        except TimeoutError as te:
            print('获取页面超时')
            time.sleep(1)
        except Exception as e:
            print(e)
            print('获取页面异常')
            time.sleep(2)


# 用request方法获取百度指数
def get_index_data(word, start, end, BaiduID):
    word_param = f'[[%7B"name":"{word}","wordType":1%7D]]'
    url = f'http://index.baidu.com/api/SearchApi/index?word={word_param}&area={BaiduID}&startDate={start}&endDate={end}'
    print(url)
    # url = f'http://index.baidu.com/api/SearchApi/index?area={BaiduID}&word={word_param}&startDate={start}&endDate={end}'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Cookie': COOKIES,
        'Host': 'index.baidu.com',
        'Connection': 'keep-alive',
        'Referer': 'http://index.baidu.com/v2/main/index.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    resp = requests.get(url, headers=headers)
    # print(resp)
    while resp.text.strip() == '':
        print('获取页面为空')
        resp = requests.get(url, timeout=10)

    while resp.status_code != 200:
        print('获取uniqid失败')
        resp = requests.get(url, timeout=10)

    # print(resp.json())
    request_status = str(resp.json().get('status'))
    request_message = str(resp.json().get('message'))

    print('\n' + word + '  城市编号:' + BaiduID + '\n' +
          'word_number:' + str(word_number) + '  BaiduID_number:' + str(BaiduID_number) +
          '  COOKIE_number:' + str(COOKIES_number) + '\n' +
          'request_status:' + request_status + '\n' + 'request_message:' + request_message)

    if request_status == '10001':
        return 0, 0, 3
    elif request_status == '10002':
        return 0, 0, 2
    elif request_status == '10000':
        return 0, 0, 5
    elif request_status == '1':
        return 0, 0, 3  # 更换cookie
    else:
        request_avg = resp.json().get('data').get('generalRatio')[0]
        request_avg1 = str(request_avg.get('all').get('avg'))
        if request_avg1 == '0':
            return 0, 0, 1
        else:
            uniqid = resp.json().get('data').get('uniqid')
            data = resp.json().get('data').get('userIndexes')[0]
            all_data = data.get('all').get('data')
            return uniqid, all_data, 0

        # 访问url可能出现的几种情况
        # status=0，avg!=0 说明正常访问且能返回非0数值
        # status=0，avg=0 说明正常访问但数据全是0，这种情况没必要留
        # status=1，no data，是种新情况，在有些cookie下会出现。这种多半是cookie被封了，返回个statuscode3从而更换cookie
        # status=10002，bad request，说明无对应词条或者该城市无对应数据
        # status=10001，request block，说明当前访问手段的cookie被封了。但人为访问可能并没有被block，意味着模拟人工访问可行
        # status=10000，not login，不确定为啥，2021年3月开始出现的这个报错

        # 自行定义statuscode及其处理手段：不是url返回值，是我方定义用来监控状态的
        # 0：一切正常
        # 1：正常访问但数据全是0，这种会直接continue，不生成csv
        # 2：无对应词条，则直接continue。如果在BaiduID=0时出现这种情况，会直接break出当前word
        # 3：cookie被封，自行更换cookie
        # 4：通过多次加载确定了是网络问题导致的request block，重跑一遍这个词
        # 5: not login，不确定是为啥


# 用selenium模拟人类登录获取百度指数
def get_index_data_selenium(word, start, end, BaiduID):
    word_param = f'[[%7B"name":"{word}","wordType":1%7D]]'
    url = f'http://index.baidu.com/api/SearchApi/index?word={word_param}&area={BaiduID}&startDate={start}&endDate={end}'
    driver.get(url)
    data_original = driver.find_element_by_xpath('/html/body').text
    data_json = json.loads(data_original)

    request_status = str(data_json.get('status'))
    request_message = str(data_json.get('message'))

    print('\n' + word + '  城市BaiduID编号:' + BaiduID + '\n' +
          'word_number:' + str(word_number) + '  BaiduID_number:' + str(BaiduID_number) +
          '  COOKIE_number:' + str(COOKIES_number) + '\n' +
          'status:' + request_status + '\n' + 'message:' + request_message)

    if request_status == '10001':
        sub_statuscode = block_check(url)
        # sub_statuscode不同取值的意义同上面statuscode的定义，这里只是一个传值参数
        return 0, 0, sub_statuscode
    elif request_status == '10002':
        return 0, 0, 2
    else:
        request_avg = data_json.get('data').get('generalRatio')[0]
        request_avg1 = str(request_avg.get('all').get('avg'))
        if request_avg1 == '0':
            return 0, 0, 1
        else:
            uniqid = data_json.get('data').get('uniqid')
            data = data_json.get('data').get('userIndexes')[0]
            all_data = data.get('all').get('data')
            return uniqid, all_data, 0


def block_check(url):
    url1 = 'http://index.baidu.com/api/SearchApi/index?area=0&word=[[%7B%22name%22:%22%E5%8C%97%E4%BA%AC%22,%22wordType%22:1%7D]]&days=30'
    limit = False
    count = 0
    while count < 5:  # 这里决定打算尝试多少次
        count = count + 1
        driver.get(url1)
        data_original_check1 = driver.find_element_by_xpath('/html/body').text
        data_json_check1 = json.loads(data_original_check1)
        request_status_check1 = str(data_json_check1.get('status'))
        driver.get(url)
        data_original_check = driver.find_element_by_xpath('/html/body').text
        data_json_check = json.loads(data_original_check)
        request_status_check = str(data_json_check.get('status'))
        if request_status_check == 10002:
            sub_statuscode_check = 2
            break
        elif request_status_check == 10001 and request_status_check1 != 10001:
            continue
        elif request_status_check == 10001 and request_status_check1 == 10001:
            print('大事不好啦！！！备用链接也失效啦！！！IP可能被封球啦！！！')
            sub_statuscode_check = 10  # 中断程序，提桶跑路
            break
        elif request_status_check == 0:
            request_avg = data_json_check.get('data').get('generalRatio')[0]
            request_avg1 = str(request_avg.get('all').get('avg'))
            if request_avg1 == '0':
                sub_statuscode_check = 1
                break
            else:
                uniqid = data_json_check.get('data').get('uniqid')
                data = data_json_check.get('data').get('userIndexes')[0]
                all_data = data.get('all').get('data')
                sub_statuscode_check = 4
                break
        else:
            print('正进行request block分支的处理，其中还有你没想到的情况，来看看咋回事？')
            sub_statuscode_check = 10  # 中断程序，提桶跑路
            break

    return sub_statuscode_check


if __name__ == '__main__':
    # ---------------------------------------------------------------------
    COOKIES_number = 32    # 初始cookie控制，可以不用改  # 程序里编号28号及以前的cookie是实验室同学们的
    word_number = 204  # 初始word控制，这个要改，初始为-1

    word_name = 'word2'
    year = 2020
    # ----------------------------------------------------------------------

    word_number_limit = 402  # 对于word_name1-3,这个值设置为402；对于word4，这个设置为4
    if word_name == 'word4':
        word_number_limit = 4

    COOKIES = Info['COOKIES'][COOKIES_number]
    invalid_COOKIES = 0
    while word_number < word_number_limit:

        word_number = word_number + 1
        word = Info[f'{word_name}'][word_number]
        BaiduID_number = -1  # 初始城市编码控制，无论如何都不要改
        while BaiduID_number < 403:
            BaiduID_number = BaiduID_number + 1
            BaiduID = Info['BaiduID'][BaiduID_number]
            start = f'{year}-01-01'
            end = f'{year}-12-31'
            print('\n' + '---------------------' + '\n' + '当前失效cookie数:' + str(invalid_COOKIES))
            try:
                uniqid, allData, statuscode = get_index_data(word, start, end, BaiduID)
            except:
                continue

            if statuscode == 4:
                BaiduID_number = BaiduID_number - 1
                print('\n' + '网络问题导致request block，重新加载已验证可行性，重跑当前城市' + '\n')
                time.sleep(5)
                continue
            elif statuscode == 3 or statuscode == 5:
                COOKIES_number = COOKIES_number + 1
                COOKIES = Info['COOKIES'][COOKIES_number]
                BaiduID_number = BaiduID_number - 1
                invalid_COOKIES = invalid_COOKIES + 1
                print('\n' + 'COOKIES被封，更换下一个' + '\n')
                time.sleep(5)
                continue
            elif statuscode == 2 and BaiduID == '0':
                print('该词条未创建，跳向下一关键词')
                break
            elif statuscode == 2 and BaiduID != '0':
                print('该城市无返回值，跳向本关键词下一城市')
                continue
            elif statuscode == 1:
                print('该城市返回值全是0，跳向本关键词下一城市')
                continue
            elif statuscode == 10:
                print('大事不好啦！！！备用链接也失效啦！！！IP可能被封球啦！！！')
                sys.exit(0)
            else:
                print('返回值非0，开始生成csv')
                ptbkData = get_ptbk(uniqid)
                resultStr1 = decrypt(ptbkData, allData)
                resultList1 = resultStr1.split(',')
                resultList = resultList1

                dataList = []
                datestart = datetime.datetime.strptime(start, '%Y-%m-%d')
                dateend = datetime.datetime.strptime(end, '%Y-%m-%d')
                while datestart <= dateend:
                    dataList.append(datestart.strftime('%Y-%m-%d'))
                    datestart += datetime.timedelta(days=1)

                pd.DataFrame({'日期': dataList, '搜索指数': resultList}).to_csv(
                    f'E:\\database\\BaiduIndex\\{year}\\{word_name}'
                    f'\\' '[' + word + '],(' + start + '至' + end + '),' + str(
                        BaiduID) + '.csv',
                    index=False,
                    encoding='gbk')
            # print(resultList)
            # print(word + str(BaiduID) + '成功')
            '''limit = False
            while allData == 0:
                count = count + 1
                if count > 3 or uniqid == 0:
                    limit = True
                    break
            if limit:
                print(word + str(BaiduID) + '失败,无对应词条')
                continue'''
