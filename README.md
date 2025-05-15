# yurihime-nyaa-downloader

一迅社的百合姬下载器

取自nyaa用户[zxc102635](https://nyaa.si/user/zxc102635)

通过爬取nyaa页面将种子信息推送至`qbittorrent` / `aria2`

## 如何使用
1. 下载本仓库
2. 进入仓库目录运行 `pip install -r requirements.txt`
3. 打开main.py修改对应配置
4. 运行`python main.py`
5. 添加定时任务即可自动下载新刊

## 如何配置

```python
PROXIES = {  # 代理配置
    'http': 'http://127.0.0.1:7897',
    'https': 'http://127.0.0.1:7897'
}

DOWNLOADER_CONFIG = {  # 下载工具配置
    'type': 'qbittorrent',  # 可选 qbittorrent 或 aria2
    'qbittorrent': {
        'host': 'http://localhost:8080', # qb的webAPI
        'username': 'admin', # qb账号
        'password': 'adminadmin' # qb密码
    },
    'aria2': {
        'rpc_url': 'http://localhost:6800/jsonrpc', # aria2的rpc地址
        'secret': 'your_secret_token' # aria2的secret
    }
}

DATE_FILE = 'last_date.txt'  # 最后日期存储文件
```
