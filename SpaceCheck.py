#!/usr/bin/env python
# encoding: utf-8
# Time    : 2/28/2019 11:54 AM
# Author  : Luzaofa

import time
import os
import logging
import shutil
import ConfigParser
from datetime import datetime
from datetime import timedelta

from Wechat import WeChat


class Config(object):
    '''解析配置文件'''

    def get_config(self, lable, value):
        cf = ConfigParser.ConfigParser()
        cf.read("CONFIG.conf")
        try:
            config_value = cf.get(lable, value)
        except:
            config_value = cf.get('root', 'name')
            print '没有找到该用户:{user}企业ID信息,请及时添加,提示信息已经发送到:{root}'.format(user=value, root=config_value)
            return 0
        return config_value


class SpaceScript(Config):
    '''文件、空间使用情况检测'''

    def __init__(self):
        super(Config, self).__init__()
        self.check_file_path = self.get_config("path", "check_file_path")  # 需要检测文件夹路径
        self.judge_day = int(self.get_config("day", "judge_day"))  # 判断条件（删除当前日期前N天的数据）
        self.max_space = int(self.get_config("space", "max_space"))  # 用户最大使用空间, 单位：G

    def log(self, fileName, mass):
        '''日志'''
        logging.basicConfig(filename=fileName, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        logging.info(mass)

    def check_file(self):
        '''检测某文件夹下的文件是否满足条件，删除不满足文件或目录'''
        files = self.get_path_files(self.check_file_path)
        drop_date = self.get_pre_date(self.judge_day)
        print '即将删除 {0} 以前编辑的所有文件或目录...'.format(drop_date)
        for file in files:
            if file[1] < drop_date:
                mass = "正在删除{mech}下的:{file}；最新编辑日期为：{mod}".format(mech=self.get_host_name(), file=file[0], mod=file[1])
                print mass
                if os.path.isfile(file[0]):
                    os.remove(file[0])  # 删除文件
                else:
                    shutil.rmtree(file[0])  # 递归删除文件夹
                wx = WeChat(self.get_config('root', 'name'))
                wx.send_data(mass)

    def get_pre_date(self, days):
        '''获取当天前N天的日期'''
        drop_time = datetime.now() - timedelta(days=days)
        return drop_time.strftime("%Y-%m-%d %H:%M:%S")

    def get_path_files(self, path):
        '''返回某文件夹下的文件'''
        answer = []
        try:
            files = os.listdir(path)
            for file in files:
                child = os.path.join(path, file)
                modifiedTime = time.localtime(os.stat(child).st_mtime)
                mTime = time.strftime('%Y-%m-%d %H:%M:%S', modifiedTime)
                answer.append([child, mTime])
            return answer
        except Exception:
            print '没有该文件夹...'
            exit(0)

    def user_used_space(self):
        '''统计当前服务器不同用户空间使用情况'''
        users = os.popen("du -h --max-depth=1 /home").readlines()
        hostname = self.get_host_name()
        answers = []
        root = self.get_config('root', 'name')
        for user in users:
            answers.append([i.replace('\t', '') for i in user.strip().split(' ') if i != ''])
        for mass in answers:
            used = mass[0].split('/')
            if len(used) == 3:
                space, user = used[0], used[-1]
                new_space = self.conversion(space)
                if new_space > self.max_space:
                    wechatuser = self.get_config("user", user)
                    if wechatuser:
                        error_mass = '{user}您好,您在{hostname}机器使用空间超出了最大限制:{max}G,目前已经使用:{used},请及时删除部分历史数据,谢谢配合...'.format(
                            user=wechatuser, hostname=hostname, max=self.max_space, used=space)
                        wx = WeChat(wechatuser)
                    else:
                        error_mass = '{root}您好,{user}在{hostname}机器使用空间超出了最大限制:{max}G,目前已经使用:{used},未找到其对应企业ID,请告知,谢谢配合...'.format(
                            root=root, user=user, hostname=hostname, max=self.max_space, used=space)
                        wx = WeChat(root)
                    wx.send_data(error_mass)
                    print error_mass
        return answers

    def conversion(self, spaceused):
        '''单位统一换算为GB'''
        used = 0
        if 'G' in spaceused:
            used = float(spaceused.replace('G', ''))
        elif 'M' in spaceused:
            used = float(spaceused.replace('M', '')) / 1024
        elif 'K' in spaceused:
            used = float(spaceused.replace('K', '')) / 1024 / 1024
        return used

    def get_host_name(self):
        '''获取服务器名'''
        hostname = os.popen("hostname").readlines()[0].replace('\n', '')
        return hostname.split('.')[0]

    def logic(self):
        '''
        业务逻辑
        :param mass:
        :return:
        '''
        if 'None' not in self.get_config("work", "file"):
            self.check_file()
        else:
            print '不需要检测文件'
        if 'None' not in self.get_config("work", "space"):
            self.user_used_space()
        else:
            print '不需要检测空间使用情况'

    def main(self):
        '''
        程序主入口
        '''
        start = time.time()
        self.logic()
        end = time.time()
        print('业务处理总耗时：%s 秒！' % (end - start))


if __name__ == '__main__':
    print 'Start！'
    demo = SpaceScript()
    demo.main()
    print 'END'
