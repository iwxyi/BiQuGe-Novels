import os
import time
import urllib.request
import re
from pip._vendor import requests


# 保存到文本文件
def save_text_file(file_name, contents):
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(contents)


# 从文本文件中读取
def read_text_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return f.read()


# 合法文件名
def filed_name(file_name):
    return file_name.replace('|', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-')\
        .replace('"', '-').replace('<', '-').replace('>', '-').replace('/', '-')


network_interval = 0.1  # 联网间隔，自动调整避免503


# 获取网页源码
def get_html(url):
    global network_interval
    res = requests.get(url)
    res.encoding = 'utf-8'
    html = res.text
    # save_text_file('./sources/latest.html', html)  # 调试用
    if html.find('503 Service Temporarily Unavailable') > -1:  # 资源无法使用，重新读取
        network_interval += 0.1
        print('（503 正在重试...）', round(network_interval, 2))
        return get_html(url)
    if network_interval > 0.1:
        network_interval *= 0.995
    return res.text


# 获取网页源码(乱码情况下改用)
def get_html2(url):
    headers = {
        'User-Agent': 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    req = urllib.request.Request(url=url, headers=headers)
    html = urllib.request.urlopen(req)
    return html.read().decode('utf-8', 'ignore')


# 获取总的网页代码
def get_total_page():
    all_source = get_html("http://www.xbiquge.la/fenlei/8_1.html")
    save_text_file("./sources/all_source.html", all_source)
    sorts = re.findall("<div class=\"novellist\">((.|\n)+?)<div class=\"clear\"></div>", all_source)
    for sort in sorts:
        get_sort_novel_list(sort[0])


# 获取每一分类的小说
def get_sort_novel_list(sort_source):
    global global_novel_count, global_novel_index
    sort_name = re.findall("<h2>(.+)</h2>", sort_source)[0]  # 名字
    novel_list = re.findall("<li><a href=\"(http://www.xbiquge.la/\\d+/\\d+/)\">(.+)</a></li>", sort_source)
    print(sort_name, len(novel_list))
    global_novel_count = len(novel_list)
    global_novel_index = 0
    for novel in novel_list:
        global_novel_index = global_novel_index+1
        get_novel(novel)  # 开始下载这部小说
    return


# 获取分类中的详细小说列表
def get_novel(novel):
    global global_novel_count, global_novel_index, global_chapter_count, global_chapter_index, network_interval
    novel_url = novel[0]   # 小说链接
    novel_name = novel[1]  # 小说名字

    if not os.path.exists("./novels/"+novel_name):
        os.makedirs("./novels/"+novel_name)

    # 如果已经爬过这小说并且完成了
    if os.path.exists("./novels/"+novel_name+"/full.txt"):
        return

    novel_source = get_html(novel_url)
    save_text_file("./sources/目录_"+novel_name+".html", novel_source)
    chapter_list = re.findall("<dd><a href=[\"\']/\\d+/\\d+/(\\d+.html)[\"\']\\s*>(.+)</a></dd>", novel_source)
    print(global_novel_index, '/', global_novel_count, "爬取小说：", novel_name, len(chapter_list), novel_url)
    global_chapter_count = len(chapter_list)
    global_chapter_index = 0

    full_novel = ""
    chapter_names = []  # 目录数组
    for chapter in chapter_list:  # 遍历每一章
        chapter_url = novel_url + chapter[0]
        chapter_name = filed_name(chapter[1])  # 使用允许的文件名
        global_chapter_index = global_chapter_index+1

        # 如果名字不符合章节格式（不是“第”开头）
        if chapter_name.find("第") != 0:
            continue

        chapter_names.append(chapter_name)

        # 如果已经爬过这章节
        if os.path.exists("./novels/"+novel_name+"/"+chapter_name+".txt"):
            full_novel += read_text_file("./novels/"+novel_name+"/"+chapter_name+".txt")
            continue

        full_novel += get_novel_chapter(novel_name, chapter_name, chapter_url)
        time.sleep(network_interval)  # 停顿一下避免503

    save_text_file("./novels/"+novel_name+"/directory.txt", '\n'.join(chapter_names))  # 保存目录
    save_text_file("./novels/"+novel_name+"/full.txt", full_novel)  # 保存整本小说
    return


# 获取小说章节
def get_novel_chapter(novel_name, chapter_name, chapter_url):
    global global_chapter_count, global_chapter_index
    print("    ", global_chapter_index, '/', global_chapter_count, "章节：", chapter_name, chapter_url)
    chapter_source = get_html(chapter_url)
    chapter_content = re.findall("<div id=\"content\">((.|\n)*)<p>", chapter_source)
    chapter_text = chapter_content[0][0].replace('<br>', '\n').replace('&nbsp;', '').replace('<br />', '')
    save_text_file("./novels/"+novel_name+"/"+chapter_name+".txt", chapter_text)
    return chapter_text


global_novel_count = 0
global_novel_index = 0
global_chapter_count = 0
global_chapter_index = 0

get_total_page()

