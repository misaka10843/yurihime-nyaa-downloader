import os
import re

import requests
from bs4 import BeautifulSoup

# ================== 配置区域 ==================
PROXIES = {  # 代理配置
    'http': 'http://127.0.0.1:7897',
    'https': 'http://127.0.0.1:7897'
}

DOWNLOADER_CONFIG = {  # 下载工具配置
    'type': 'qbittorrent',  # 可选 qbittorrent 或 aria2
    'qbittorrent': {
        'host': 'http://localhost:8080',
        'username': 'admin',
        'password': 'adminadmin'
    },
    'aria2': {
        'rpc_url': 'http://localhost:6800/jsonrpc',
        'secret': 'your_secret_token'
    }
}

DATE_FILE = 'last_date.txt'  # 最后日期存储文件


# =============================================

class Downloader:
    @staticmethod
    def send_to_qbittorrent(magnet_links):
        from qbittorrentapi import Client
        try:
            client = Client(
                host=DOWNLOADER_CONFIG['qbittorrent']['host'],
                username=DOWNLOADER_CONFIG['qbittorrent']['username'],
                password=DOWNLOADER_CONFIG['qbittorrent']['password']
            )
            for link in magnet_links:
                client.torrents_add(urls=link)
            print(f"成功添加 {len(magnet_links)} 个任务到 qBittorrent")
        except Exception as e:
            raise Exception(f"qBittorrent 添加失败: {str(e)}")

    @staticmethod
    def send_to_aria2(magnet_links):
        try:
            for link in magnet_links:
                payload = {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "aria2.addUri",
                    "params": [
                        f"token:{DOWNLOADER_CONFIG['aria2']['secret']}",
                        [link]
                    ]
                }
                response = requests.post(
                    DOWNLOADER_CONFIG['aria2']['rpc_url'],
                    json=payload
                )
                if response.json().get('error'):
                    raise Exception(response.json()['error'])
            print(f"成功添加 {len(magnet_links)} 个任务到 Aria2")
        except Exception as e:
            raise Exception(f"Aria2 添加失败: {str(e)}")


def parse_date(name):
    """从名称解析标准化日期 (YYYY.MM)"""
    match = re.search(r'(\d{4})年(\d{1,2})月号', name)
    if not match:
        return None
    year, month = match.groups()
    return f"{year}.{int(month):02d}"  # 强制转换为两位数月份


def get_base_date():
    """获取基准日期（优先读取保存的日期）"""
    if os.path.exists(DATE_FILE):
        with open(DATE_FILE, 'r') as f:
            return f.read().strip()
    return input("请输入基准日期 (格式: YYYY.MM): ")


def save_last_date(date_str):
    """保存最后处理的日期"""
    with open(DATE_FILE, 'w') as f:
        f.write(date_str)


def main():
    # 获取基准日期
    base_date = get_base_date()
    print(f"当前基准日期: {base_date}")

    # 获取页面数据
    print("正在获取页面数据...")
    try:
        response = requests.get('https://nyaa.si/user/zxc102635', proxies=PROXIES)
        response.raise_for_status()
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return

    # 解析数据
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select('table.torrent-list tbody tr.default')

    # 处理有效条目
    valid_entries = []
    for row in rows:
        try:
            name = row.select_one('td:nth-child(2) a:last-child').get_text(strip=True)
            magnet = row.select_one('td:nth-child(3) a[href^="magnet:"]')['href']
        except:
            continue

        if not re.search(r'コミック百合姫 \d{4}年\d{1,2}月号', name):
            continue

        date_str = parse_date(name)
        if not date_str:
            continue

        # 日期筛选
        if date_str > base_date:
            valid_entries.append({
                'name': name,
                'magnet': magnet,
                'date': date_str
            })

    if not valid_entries:
        print("没有需要处理的新条目")
        return

    # 按日期排序并获取最新日期
    valid_entries.sort(key=lambda x: x['date'])
    last_date = valid_entries[-1]['date']
    magnet_links = [e['magnet'] for e in valid_entries]

    # 发送到下载工具
    print(f"找到 {len(magnet_links)} 个新条目，最新日期: {last_date}")
    try:
        if DOWNLOADER_CONFIG['type'] == 'qbittorrent':
            Downloader.send_to_qbittorrent(magnet_links)
        elif DOWNLOADER_CONFIG['type'] == 'aria2':
            Downloader.send_to_aria2(magnet_links)
    except Exception as e:
        print(str(e))
        return

    # 保存最后日期
    save_last_date(last_date)
    print("任务处理完成，已更新基准日期")


if __name__ == '__main__':
    main()
