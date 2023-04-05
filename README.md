# CXW-SZJXY

Another script for University Task.

又一个自动化脚本，解决学校任务。


## Background

时政进校园从浙江新闻迁移到了潮新闻 - -

## Usage

1. Git clone this repo.
    ```bash
   git clone https://github.com/Mas0nShi/CXW-SZJXY
   cd CXW-SZJXY
    ```
2. Copy the config file.
    ```bash
    cp cxw/config.example.toml cxw/config.toml
    ```
3. Edit the config file.
    ```toml
   [device]
   [device.headers]
   user-agent = "zjolapp; 5.0.4 ***"                   # 自行抓包获取
   custom-user-agent = "Mozilla*** ; zjolapp; 5.0.4"   # 自行抓包获取
   [answer]
   location = "杭州"                                    # 你的位置
   [user]
   session-id = ""                                     # 自行抓包获取
   account-id = ""                                     # 自行抓包获取
   [bot]
   [bot.lark]                                          # 可选, 使用飞书群组自定义机器人 
   webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/***"
   secret = "7NzsOQPZMtgjVvPjEQnQtf"
   ```

4. Run the script.
    ```bash
    python3 cxw-szjxy.py
    ```

## Features

- [x] 自动答题
- [x] 推送答案到飞书群组
- [x] 缓存已答题目，避免重复答题

## License

[MIT](LICENSE)

