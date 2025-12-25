from concurrent.futures import ThreadPoolExecutor
import sys
from bs4 import BeautifulSoup
import requests
import json
from urllib.request import urlretrieve
import os
import time
import threading


def post(URL:str, DATA=None, HEADERS:dict=None):
    return requests.post(url=URL,data=DATA,headers=HEADERS).text

def get(URL:str, PARAMS=None, HEADERS:dict=None):
    return requests.get(url=URL,params=PARAMS,headers=HEADERS).text
# [\t !"#$%&\'()*\-/<=>?@\[\\\]^_`|,.:]+
# 规范化文件名
nameErr_str = '\t !"#$%&\'()*\-/<=>?@\[\\\]^_`|,.:'
def standardization_filename(filename:str):
    for i in range(len(nameErr_str)):
        filename = filename.replace(nameErr_str[i],'')
    return filename

music_url_list = list()
music_name_list = list()
musichtml_url_list = list()
start_url_list = list()
host = 'http://www.2t58.com'
# start_url = "http://www.2t58.com/singer/d25ka3M.html"
api_url = 'http://www.2t58.com/js/play.php'
requests.adapters.DEFAULT_RETRIES = 50

# http://www.2t58.com/singer/d25ka3M.html 总29页

def get_mp3name_formHTML(HTMLurl:str):
    htmldata = get(HTMLurl,{'Connection': 'close'})
    page = BeautifulSoup(htmldata, "html5lib")
    return page.find('div',attrs={"class":"djname"}).find('h1').text


def get_mp3id_formHTML(HTMLurl:str):
    htmldata = get(HTMLurl)
    page = BeautifulSoup(htmldata, "html5lib")
    return page.find('a',attrs={"class":"layui-btn lkbtn"})['onclick'].split('\'')[1].split('\'')[0]

def get_mp3url_formHTML(HTMLurl:str):
    api_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer':HTMLurl
    }
    jsondata = post(api_url,'id=' + get_mp3id_formHTML(HTMLurl) + "&type=music",api_header)
    return json.loads(jsondata)['url']



print('【此脚本将会自动下载此链接下所有该歌手的音乐】')

if len(sys.argv) > 1:
    download_path = sys.argv[1]
    start_url = sys.argv[2]
    thread_number = sys.argv[3]
else:
    start_url = input('请输入' + host + '网站内的任意一歌手页面url，脚本将会免费下载他的所有音乐:')
    try:
        err_check_temp = start_url.split('/')[len(start_url.split('/')) - 1].split('.html')[0]
        try:
            int(err_check_temp)
            print('检测到非歌手首页，智能矫正URL路径')
            start_url = start_url.replace('/' + err_check_temp, '')
        except Exception as urlerr:
            # print(urlerr)
            pass
    except:
        pass
    

    download_path = input('请输入爬虫下载文件保存路径：') # D:/泽野弘之爬虫歌曲下载/ D:/测试一爬虫歌曲下载/ D:/初音未来爬虫歌曲下载
    if download_path[len(download_path)-1] != '/':
        download_path += '\\'
    if not os.path.exists(download_path):
        print("路径不存在，已自动创建")
        os.makedirs(download_path)
    thread_number = int(input('请输入下载线程数:'))
# http://www.2t58.com/singer/d2RoZA.html


print(start_url)
main_page_text = get(start_url)
main_page = BeautifulSoup(main_page_text, "html5lib")

page_number = int(main_page.find('a',attrs={'class':'lkpc'})['href'].split('/')[len(main_page.find('a',attrs={'class':'lkpc'})['href'].split('/'))-1].split('.')[0])
for file_count in range(page_number):
    start_url_list.append(start_url.replace('.html','/' + str(file_count+1)) + '.html')

num = 0
for x in range(len(start_url_list)):
    start_page = BeautifulSoup(get(start_url_list[x]), "html5lib")
    music_li_tag = start_page.find('div',attrs={'class':'play_list'}).find_all('li')
    for file_count in range(len(music_li_tag)):
        musichtml_url_list.append(music_li_tag[file_count].a['href'])
        music_name_list.append(music_li_tag[file_count].a.text)
        print('正在检索第' + str(num + file_count)+ '首歌曲...')
    num += file_count

music_count = len(musichtml_url_list)
    
try:
    file_count = int(open(download_path + 'record.txt', 'r+').read())-1
except Exception as mainerr:
    file_count = 0
    print(mainerr)

def download_process(redownload_number:int=None):
    global file_count
    global flag

    if redownload_number == None:
        this_download_number = file_count
        file_count += 1
    else:
        this_download_number = redownload_number
    try:
        url = host + musichtml_url_list[this_download_number]
        print('正在下载第' + str(this_download_number) + '/' + str(music_count) + '首歌曲[' + music_name_list[this_download_number] +']...')
        mp3_url = get_mp3url_formHTML(url)
        save_path = download_path + standardization_filename(music_name_list[this_download_number])
        all_file = os.listdir(download_path)

        if save_path.split('\\')[len(save_path.split('\\'))-1]+'.mp3' in all_file:# 防重名措施
            print('跳过重名歌曲：' + music_name_list[this_download_number] + '(' + str(len(all_file)) + '有效数量)')
            flag -= 1
            return None
        try:
            urlretrieve(mp3_url, save_path + '.mp3')
            # time.sleep(0.5)
        except Exception as err:
            print(err)
        print(str(this_download_number) + '/' + str(music_count) + '首歌曲[' + music_name_list[this_download_number] +']完成下载(' + str(len(all_file)-1) + '有效数量)')
        open(download_path + 'record.txt', 'w+').write(str(this_download_number))
        flag -= 1
    except Exception as mainerr:
        print(mainerr)
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '发生错误')
        print('第' + str(this_download_number) + '/' + str(music_count) + '首歌曲[' + music_name_list[this_download_number] +']发生错误，重启该下载')
        # os.system('python ' + sys.argv[0] + ' \"' + download_path + ' ' + start_url + ' ' + str(thread_number) + '\"')
        download_process(this_download_number)
        return None

executor = ThreadPoolExecutor(max_workers=thread_number)
flag = 0
while file_count in range(file_count, music_count):
    if flag < thread_number:
        time.sleep(0.1)
        executor.submit(download_process)
        flag += 1
    else:
        time.sleep(1)

# G:\水培社项目\python教学试点\宣传项目\复杂2_网络爬虫.bat
