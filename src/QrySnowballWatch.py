import os
import requests
import json
from datetime import datetime
from pathlib import Path


# todo 登录后浏览器获取xq_a_token
# ios手机可用stream抓取app上的xq_a_token和uid：u
def set_xueqiu_token(token, u):
    """手动设置 xq_a_token 和 u"""
    os.environ["XQ_A_TOKEN"] = token
    os.environ["XQ_U"] = u


# 读取本地文件雪球用户名
def load_cname(file_path):
    cname_list = None
    # 读取 cname.txt 文件内容，存入列表
    with open(file_path, "r", encoding="utf-8") as file:
        cname_list = [line.strip() for line in file if line.strip()]  # 去除首尾空白行
    if cname_list:
        return cname_list
    else:
        raise ValueError('请先将完整雪球用户名写入files/cname.txt中，以换行分隔')


# 获取自选股
# https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?category=1&size=1000&uid=3598214045
def get_user_watchstock(token, u, uid):
    """获取雪球用户所有好友的 screen_name（自动翻页）"""
    url = f"https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?category=1&size=1000&uid={uid}"
    headers = {
        "Accept": "application/json",
        "Cookie": f"xq_a_token={token}; u={u}",
        "User-Agent": "Xueqiu iPhone 14.15.1",
        "Accept-Language": "zh-Hans-CN;q=1, ja-JP;q=0.9",
        "Accept-Encoding": "br, gzip, deflate",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # 获取 stocks 列表
        stocks = data.get("data", {}).get("stocks", [])

        # 按照watched数值从大到小排列（最近关注放第一）：关注时间的毫秒值
        sorted_stocks = sorted(stocks, key=lambda x: x["watched"], reverse=True)

        # 提取 name股票名 和 symbol代号，并将watched数值（时间毫秒值）还原成时间，最后拼接为字符串，放进列表
        result = [
            f"{stock['name']} ({stock['symbol']}) - {datetime.fromtimestamp(stock['watched'] / 1000).strftime('%Y-%m-%d %H:%M:%S')}"
            for stock in sorted_stocks
        ]
        return result
    else:
        print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
        return None


# 获取关注列表
# https://xueqiu.com/friendships/groups/members.json?uid=3598214045&page=1&gid=0
def get_xueqiu_friends_all(token, u, uid):
    """获取雪球用户所有好友的 screen_name（自动翻页）"""
    url = "https://xueqiu.com/friendships/groups/members.json"
    page = 1
    all_screen_names = []

    headers = {
        "Accept": "application/json",
        "Cookie": f"xq_a_token={token}; u={u}",
        "User-Agent": "Xueqiu iPhone 14.15.1",
        "Accept-Language": "zh-Hans-CN;q=1, ja-JP;q=0.9",
        "Accept-Encoding": "br, gzip, deflate",
        "Connection": "keep-alive",
    }

    # 自动翻页查询
    print("\n正在分页查询关注列表...")
    while True:
        params = {"page": page, "gid": 0, "uid": uid}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"请求失败: {response.status_code}, 响应: {response.text}")
            break

        data = response.json()  # 所有返回数据
        users = data.get("users", [])
        max_page = data.get("maxPage", page)  # 取 maxPage，防止无限翻页

        all_screen_names.extend(user["screen_name"] for user in users)
        print(f"第 {page} 页，获取 {len(users)} 条数据")

        if page >= max_page:  # 当达到 maxPage 时停止
            break
        page += 1

    return all_screen_names


# 根据用户名查询uid
def get_userid_by_cname(token, u, cname):
    """获取雪球用户的uid"""
    url = f"https://xueqiu.com/query/v1/search/user.json?count=20&page=1&q={cname}"
    headers = {
        "Accept": "application/json",
        "Cookie": f"xq_a_token={token}; u={u}",
        "User-Agent": "Xueqiu iPhone 14.15.1",
        "Accept-Language": "zh-Hans-CN;q=1, ja-JP;q=0.9",
        "Accept-Encoding": "br, gzip, deflate",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        respon_json = response.json()
        # print(respon_json)
        return get_target_id(respon_json, cname)
    else:
        print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")

        return None


# 处理上方根据用户名查询uid
def get_target_id(respon_json, target_name):
    if respon_json.get("code") == 200 and "data" in respon_json:
        for data_item in respon_json["data"]:
            if "list" in data_item:
                for item in data_item["list"]:
                    if item.get("screen_name") == target_name:
                        return str(item.get("id"))  # 转换为字符串返回
    return None  # 如果没找到，返回 None


# 处理结果:读取本地文件
def load_previous_result(file_path):
    """从本地文件加载上次保存的 stocks 列表"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()  # 读取并去除空白字符
                if not content:
                    return []  # 文件为空，返回空列表
                return json.loads(content)
        except json.JSONDecodeError:
            print("文件 JSON 解析错误，已重置为空！")
            return []  # 解析失败，返回空列表
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            return []  # 发生其他错误时，返回空列表
    return []  # 如果文件不存在，返回空列表


# def ensure_directory_exists(file_path):
#     """确保文件所在的目录存在"""
#     directory = file_path.parent # file_path必须文件类型，不能str
#     if not directory.exists():
#         directory.mkdir(parents=True, exist_ok=True)


def save_current_result(file_path, result):
    # 确保目录存在
    # ensure_directory_exists(file_path)
    """将当前 stocks 列表保存到本地文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def compare_results(old_result, new_result):
    """比较两个列表，找出新增和减少的元素。但是无序的"""
    old_set = set(old_result)
    new_set = set(new_result)

    added = new_set - old_set  # 新增的
    removed = old_set - new_set  # 减少的

    return list(added), list(removed)


# 读取本地文件，比较两次程序运行后，发生变化的列表元素。 file是文件，不是str，没有rsplit方法
def file_diff(name, file, result):
    # 读取本地存储的上次结果
    previous_result = load_previous_result(file)
    # 比较新旧结果
    added, removed = compare_results(previous_result, result)
    # 如果有变化，打印变更信息并更新本地文件
    if added or removed:
        if added:
            print("新增的关注:", added)
            # added文件名处理：按最后一个 "." 分割，确保只分割扩展名
            name_part, ext = str(file).rsplit('.', 1)
            # 在文件名前添加 "_add"，并拼接回扩展名
            added_file = f"{name_part}_add.{ext}"  # file = stocksMo_add.json
            # todo 如有设置tg，推送到tg（或微信）
            send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, f'{name}新增关注或自选:{added}')
            # send_msg(PUSH_TOKEN, f'{name}新增关注或自选', added)
            save_current_result(added_file, added)
        if removed:
            print("减少的关注:", removed)
            # added文件名处理：按最后一个 "." 分割，确保只分割扩展名
            name_part, ext = str(file).rsplit('.', 1)
            # 在文件名前添加 "_add"，并拼接回扩展名
            rm_file = f"{name_part}_rm.{ext}"  # file = stocksMo_rm.json
            save_current_result(rm_file, removed)

        # 保存最新结果
        save_current_result(file, result)
    else:
        print("关注列表无变化，无需更新。")


# github工作流和本地运行，产生的文件放在不同的目录。（gitignore忽略本地运行的目录的文件；工作流运行产生的文件不忽略，让其自动推送到仓库）
def create_output_directory():
    # 检查环境变量以确定当前的运行环境。github工作流产生文件放在workflow_files下
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = 'files/workflow_files/'
    else:
        output_dir = 'files/local_files/'

    # 创建目录（如果不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return output_dir


# 消息推送微信pushplus：需要1元实名认证费用
def send_msg(p_token, title, content):
    if p_token is None:
        return
    url = 'http://www.pushplus.plus/send'
    r = requests.get(url, params={'token': p_token,
                                  'title': title,
                                  'content': content})
    print(f'通知推送结果：{r.status_code, r.text}')


# 推送tg消息
def send_telegram_message(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        return
    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(tg_url, json=data)
    if response.status_code == 200:
        print("消息推送成功!")
    else:
        print("Failed to send message. Status code:", response.status_code)


# 本地运行，需要关闭vpn才可以！！！ 。每次提交github前，先从github拉取一次，获取最新的workflow产生的json。
if __name__ == "__main__":

    # todo 也可set_xueqiu_token方法手动设置 token和自己的uid，也可以环境变量设置
    # set_xueqiu_token("xxxc", "3xxxx")

    # 环境变量获取token，u。
    xq_a_token = os.getenv("XQ_A_TOKEN")
    u = os.getenv("XQ_U")
    if not xq_a_token or not u:
        raise ValueError("请先设置 xq_a_token 和 u")

    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
    TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
    # PUSH_TOKEN = os.environ.get("PUSHPLUS_KEY")

    # 读取文件中的雪球用户名
    cname_path = Path(__file__).parent / "files/cname.txt"  # 工作流运行目录Path(__file__).parent ，即src目录
    cname_list = load_cname(cname_path)
    for cname in cname_list:
        print(f'\n正在查询用户：【{cname}】的自选股和关注列表....')
        user_id = get_userid_by_cname(xq_a_token, u, cname)
        if not user_id:
            print(f"请求失败。请检查files/cname.txt里雪球用户名，必须准确!")
            continue

        # 查询某用户自选股
        watchstock = get_user_watchstock(xq_a_token, u, user_id)
        print(watchstock)

        # 获取user_id后4为作为文件名区分不同查询用户的文件
        userid_tail = user_id[-4:]
        # 便于分清部分已知用户：莫大、边大、罗洄头
        user_file_name = None
        if userid_tail == '4045':
            user_file_name = 'Mo'
        elif userid_tail == '7947':
            user_file_name = 'Bian'
        elif userid_tail == '1661':
            user_file_name = 'Luo'
        else:
            user_file_name = cname

        output_dir = create_output_directory()
        # 本地股票文件--stocksMo.json内容以最新关注为首先后排序，而add新增关注则无序。
        stocks_file = Path(__file__).parent / f"{output_dir}stocks{user_file_name}.json"
        file_diff(cname, stocks_file, watchstock)  # 比较是否有新增关注股票

        # 查询某用户的关注列表
        all_names = get_xueqiu_friends_all(xq_a_token, u, user_id)
        print(f"总共获取到 {len(all_names)} 个好友")
        # print(f"总共获取到 {len(all_names)} 个好友名称：{all_names}")

        # 本地关注列表文件
        watch_list_file = Path(__file__).parent / f'{output_dir}/watchlist{user_file_name}.json'
        file_diff(cname, watch_list_file, all_names)  # 比较是否有新增关注用户
