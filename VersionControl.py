import os
import shutil
import argparse
import getpass


def mkdir(path):
    path = path.strip()
    path = path.rstrip("\\")
    exist = os.path.exists(path)
    if not exist:
        os.makedirs(path)
    else:
        return


def is_number(input):
    try:
        result = int(input)
    except:
        result = 0
    return result


def get_file_number(path):
    dir_list = []
    for dirs in os.listdir(path):
        dir_list.append(dirs)
    return len(dir_list)


def read_OK_build():  # 读取下面这个地址的最新的完整build
    with open(f'{net_path}/LastGood/buildOK.txt', 'r') as f:
        ok = f.readline(4).strip('\n')
    return ok


def get_latest_build_number(path):
    dir_list = []
    for dirs in os.listdir(path):
        dir_list.append(dirs)
    dir_list_new = list(filter(is_number, dir_list))  # 去除文件名中的非数字项
    if dir_list_new:
        latest_build_number = max(dir_list_new)
    else:
        latest_build_number = 0
    return latest_build_number


def start_earth(build):
    if build is None:
        latest_build_number = get_latest_build_number(local_path)
        start_build = f'{local_path}\\{latest_build_number}\\Portable\\bin\\ArcGISEarth.exe'
        print('Initiating the latest Build: ' + latest_build_number)
    else:
        start_build = f'{local_path}\\{build}\\Portable\\bin\\ArcGISEarth.exe'
        if os.path.isfile(start_build):
            print('Initiating assigned Build: ' + build)
        else:
            print('This build does not exist, please check.')
            return 0
    # print('路径：' + start_build)
    os.system("start explorer %s" % start_build)


def update(build):
    if build is None:
        latest_local = str(get_latest_build_number(local_path))
        latest_network = read_OK_build()
        if latest_network > latest_local:
            print('New version detected: ' + latest_network + '. Copying, do not close the program.')
            shutil.copytree(f'{net_path}/{latest_network}',
                            f'{local_path}\\{latest_network}')
            print('Copying completed.')
        elif latest_network == latest_local:
            print('Local version already up-to-date. latest version: ' + latest_local)
        else:
            print('Exception occurred, please check or reset.' + '\n' + 'Latest Local Version: ' + latest_local + '\n' + 'Latest Network Version: ' + latest_network)
    else:
        print('Copying, do not close the program.')
        try:
            shutil.copytree(f'{net_path}/{build}',
                            f'{local_path}\\{build}')
            print('Copying completed, Build ' + build + ' now exists on local disk.')
        except:
            print('Exception occurred, possibly because the version already exists on local.')


def clear(build):  # 清理C盘的config和workspace，以及替换安装目录的config
    if build is None:
        target_build_number = get_latest_build_number(local_path)
    else:
        target_build_number = build

    try:
        shutil.copy(f'{net_path}/{target_build_number}/Portable/bin/config.xml',
                    f'{local_path}\\config.xml')
    except:
        print('Internet error, proceed with existing config.xml.')

    print('Clearing Build: ' + target_build_number)
    try:
        os.remove(f'C:\\Users\\{username}\\AppData\\Roaming\\ESRI\\ArcGISEarth\\config.xml')
        shutil.rmtree(f'C:\\Users\\{username}\\Documents\\ArcGISEarth\\workspace')
    except:
        print('Files in C Disk already removed.')
    shutil.copy(f'{local_path}\\config.xml', f'{local_path}\\{target_build_number}\\Portable\\bin\\config.xml')

    print('1: Successfully deleted config.xml' + '\n' + '2: Successfully cleared workspace' + '\n'
          + '3: Successfully overridden installation-path-config using default config' + '\n'
          + '-----Clearance Process Completed-----')


def open_config(build):
    if build is None:
        target_build_number = get_latest_build_number(local_path)
    elif build == 'c':
        print('Opening C-disk config:' + f'C:\\Users\\{username}\\AppData\\Roaming\\ESRI\\ArcGISEarth\\config.xml')
        os.system("start explorer %s" % f'C:\\Users\\{username}\\AppData\\Roaming\\ESRI\\ArcGISEarth\\config.xml')
        return
    else:
        target_build_number = build
    print('Opening config.xml, Build: ' + target_build_number)
    os.system("start explorer %s" % f'{local_path}\\{target_build_number}\\Portable\\bin\\config.xml')


def build_list():
    path_list = [local_path, net_path]
    for path in path_list:
        dir_list = []
        print('---------------------------------------------' + '\n' + path + '\n' + '---------------------------------------------')
        for dirs in os.listdir(path):
            dir_list.append(dirs)
        dir_list_new = list(filter(is_number, dir_list))  # 去除文件名中的非数字项
        print(str(dir_list_new))


if __name__ == '__main__':
    local_path = 'D:\\ArcGIS_Earth_Testrun\\DailyBuild'     # 建议把所有DailyBuild一起放在一个文件夹
    net_path = '//earth-bj-data/ArcGISEarth/Builds/DailyBuild'
    try:
        mkdir(local_path)
    except:
        local_path = 'C:\\ArcGIS_Earth_Testrun\\DailyBuild'
        mkdir(local_path)

    username = getpass.getuser()
    passcode = False
    print(f'Welcome, {username}. How\'s your day?')
    print('Actions Supported: start, config, clear, update, list, exit\n')

    while not passcode:
        command = input('Input Command: ')
        command = command.split()  # 在这里command变成了列表
        if len(command) == 1:
            act = command[0]
            bd = None
        elif len(command) == 2:
            act = command[0]
            bd = command[1]
        else:
            print('[Warning] Wrong input format\n')
            continue

        if act == 'start':
            start_earth(bd)
        elif act == 'clear':
            clear(bd)
        elif act == 'update':
            update(bd)
        elif act == 'config':
            open_config(bd)
        elif act == 'list':
            build_list()
        elif act == 'exit':
            passcode = True
        else:
            print('[Warning] Wrong input format\n')
            continue
        print('\n')

    # -------------------命令说明---------------------------------------------------------

    # -act  指定执行操作类型
    # -act start        检测local_path的所有build版本，然后启动最新版本
    # -act clear        删除C盘的config、删除document的workspace、重置安装目录的config。    注：portal相关属于敏感信息所以无法访问
    # -act update       检查earth-bj-data的DailyBuild路径中的最新版本号，与本机进行对比，如果有更新版本则会自动复制更新
    # -act config       打开config.xml文件的最新版本

    # -bd   指定版本号
    # 以上指令如果没有指定版本号默认使用 local_path 的最新版本，如果指定了就会使用指定版本
    # -act list         列出当前本机、网络所拥有的全部版本号，可以借此判断本机需不需要更新

    # ------------------terminal代码（可以直接复制）------------------------------------------

    # tip：使用terminal前先cd到存放verman.py的文件夹
    # 首先直接输入“D:”进入D盘，然后使用下面的语句进入具体文件夹
    # cd D:\20210317_HumanSimulate

    # 使用指令进行操作
    # python verman.py -act start
    # 如果需要指定版本，使用以下格式
    # python verman.py -act update -bd 0000

    # tip：指令可以通过键盘↑↓箭头实现复用

    # ---------------------下面的代码是针对使用控制台进行控制的初始化--------------------------------------------------------

    # parser = argparse.ArgumentParser(description='mode selection')
    # parser.add_argument('-act', help='define action', required=True)
    # parser.add_argument('-bd', help='define build', required=False)
    # parser.add_argument('-m', help='define mode', required=False)
    # args = parser.parse_args()
    #
    # if args.act == 'start':
    #     start_earth(args.bd)
    # elif args.act == 'clear':
    #     clear(args.bd)
    # elif args.act == 'update':
    #     update(args.bd)
    # elif args.act == 'config':
    #     open_config(args.bd)
    # elif args.act == 'list':
    #     build_list()
    # elif args.act == 'test':
    #     test()


