import os
import requests
import json
from datetime import datetime
import configparser
from pathlib import Path

# 此程序在gcp-tw上每6分钟抛

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


def send_xq_get(token, u, url):
    # url = f"https://xueqiu.com/statuses/original/timeline.json?user_id={uid}&page=1&count=10&md5__1038={md5}"
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
        return data
    else:
        print(f"请求失败，状态码: {response.status_code}, 响应: {response.text}")
        return None


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
    return None  # 如果文件不存在，返回空列表


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
def file_diff(cname, file, result):
    # 读取本地存储的上次结果
    previous_result = load_previous_result(file)
    # 如果列表不是None（不是第一次运行）
    if previous_result is not None:
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
                send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, f'【{cname}】 新增关注或自选:{added}')
                send_wx_msg(PUSH_TOKEN, f'【{cname}】 新增关注或自选', added)
                save_current_result(added_file, added)
            if removed:
                print("减少的关注:", removed)
                # added文件名处理：按最后一个 "." 分割，确保只分割扩展名
                name_part, ext = str(file).rsplit('.', 1)
                # 在文件名前添加 "_add"，并拼接回扩展名
                rm_file = f"{name_part}_rm.{ext}"  # file = stocksMo_rm.json
                send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, f'【{cname}】 减少的关注或自选:{removed}')
                send_wx_msg(PUSH_TOKEN, f'【{cname}】 新增关注或自选', removed)
                save_current_result(rm_file, removed)
        else:
            print("关注列表无变化，无需更新。")
    # 保存最新结果
    save_current_result(file, result)


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
def send_wx_msg(p_token, title, content):
    if p_token is None:
        return
    url = 'http://www.pushplus.plus/send'
    r = requests.get(url, params={'token': p_token,
                                  'title': title,
                                  'content': content})
    print(f'微信推送结果：{r.status_code, r.text}')


# 推送tg消息
def send_telegram_message(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        print('没有配置tg机器人，无法推送')
        return
    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(tg_url, json=data)
    if response.status_code == 200:
        print("tg消息推送成功!")
    else:
        print("Failed to send message. Status code:", response.status_code)


# 处理某用户“发文专栏”响应中的json 并推送新增发文：每个文章id唯一，通过id判断是否已经存在该文章，若不存在则判断为新增，推送。
def deal_timeline(json_data, file_all, file_add, msg_token,username):
    # 提取文章 ID、标题和描述
    new_items = []
    for item in json_data.get("list", []):
        post_id = str(item.get("id"))
        title = item.get("title", "").strip()
        time_str = item.get("timeBefore", "").strip()
        desc = item.get("description", "").strip().replace("<br/>", "\n")
        content = f"{time_str},{title}\n{desc}\n"
        new_items.append((post_id, content))  # new_items是列表，但每个元素是元组，仍有01索引，0为id，1为content，后方截取简短关键字符串时，要注意
    if len(new_items) != 0:
        print(f'\n{NOW}，此次“发文专栏”响应第一个元素为：{new_items[0][0]}，{new_items[0][1][:15]}')  # new_items列表第一个元素是元组，元组的第一个元素是id，第二个元素截取前15个字符，不够15打印全部
    else:
        print(f'\n{NOW}，【“发文专栏”响应异常！！！检查token和md5！！！】')

    # 获取历史记录中的 ID（来自 file_all）
    existing_ids = set()
    if os.path.exists(file_all):
        with open(file_all, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID:"):
                    existing_ids.add(line.strip().split(":", 1)[1])

    # 分别写入 result.txt（file_all全部） 和 add.txt（file_add新增）
    with open(file_all, "a", encoding="utf-8") as result_file, \
            open(file_add, "w", encoding="utf-8") as add_file:
        for post_id, content in new_items:
            entry = f"ID:{post_id}\n{content}\n---\n"
            if post_id not in existing_ids:
                add_file.write(entry)  # 只写新增部分
                send_wx_msg(msg_token, f'【{username}】专栏文章新增：', entry)  # todo 发送微信推送，第一次运行内容太多，先屏蔽以下2行推送
                send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, f'【{username}】专栏文章新增：{entry}')  # tg推送
                result_file.write(entry)  # 新增也写入总记录

    print(f"✅《专栏》处理完成。新增内容（如有）写入 {file_add}，全部记录写入 {file_all}。")


# 处理某用户“发文、回复”响应中的发文的json 并推送新增发文
def deal_reply_text(json_data, file_all, file_add, msg_token,username):
    # 读取历史记录中的 ID（避免重复）
    existing_ids = set()
    if os.path.exists(file_all):
        with open(file_all, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID:"):
                    existing_ids.add(line.strip().split(":", 1)[1])

    # 处理数据
    new_entries = []
    for item in json_data.get("statuses", []):
        post_id = str(item.get("id"))
        description = item.get("description", "")
        title = item.get("title", "").strip()
        text = item.get("text", "").strip()
        time_str = item.get("timeBefore", "").strip()

        # 过滤规则：跳过含“回复”或“@”的内容
        if "回复" in description and "@" in description:
            continue

        # 如果是新 ID，则加入结果列表
        if post_id not in existing_ids:
            entry = f"ID:{post_id}\n标题：{time_str},{title}\n{text}\n---\n"
            new_entries.append((post_id, entry))

    # 写入文件
    with open(file_all, "a", encoding="utf-8") as result_file, \
            open(file_add, "w", encoding="utf-8") as add_file:
        for post_id, entry in new_entries:
            result_file.write(entry)
            send_wx_msg(msg_token, f'【{username}】新增发文/回复：', entry)  # todo 发送微信推送，第一次运行内容太多，先屏蔽以下2行推送
            send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, f'【{username}】新增发文/回复：：{entry}')
            add_file.write(entry)

    print(f"✅《发文/回复》处理完成。本次新增 {len(new_entries)} 条，已写入 {file_add} 和 {file_all}。")


# 本地运行，需要关闭vpn才可以！！！ 。每次提交github前，先从github拉取一次，获取最新的workflow产生的json。
"""
罗洄头：uid=2632831661   我uid=3525189939  莫大：uid =3598214045  边大：2093337947   我安卓：6174823224
"""
if __name__ == "__main__":
    # 切换当前工作目录为脚本所在目录 --服务器部署cron执行调度时有用
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 当前时间
    NOW = datetime.now()

    # 读取本地配置文件,初始化配置读取器
    config = configparser.ConfigParser(interpolation=None)  # # 禁用 % 插值，避免%字符报错
    config.read("xq_config.ini", encoding="utf-8")

    # 读取参数
    xq_a_token = config.get("xueqiu", "xq_a_token", fallback="")
    u = config.get("xueqiu", "u", fallback="")
    timeline_md5 = config.get("xueqiu", "timeline_md5", fallback="")
    text_reply_md5 = config.get("xueqiu", "text_reply_md5", fallback="")
    pushplus_token = config.get("msg", "pushplus_token", fallback="")
    TG_BOT_TOKEN = config.get("msg", "TG_BOT_TOKEN", fallback="")
    TG_CHAT_ID = config.get("msg", "TG_CHAT_ID", fallback="")

    # todo 也可set_xueqiu_token方法手动设置 token和自己的uid，也可以环境变量设置
    set_xueqiu_token("c8c766e10f8c053892f137f9d67e8dcf38d0e1d9", "6174823224")  # 我uid：3525189939

    # 环境变量获取推送机器人，暂时未用，上方配置文件中读取
    # TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    # TG_CHAT_ID = os.getenv("TG_CHAT_ID")
    PUSH_TOKEN = os.getenv("PUSHPLUS_KEY")  # 微信pushplus推送未用到，用了tg，有需要可自行取消此行及200行注释启用

    # uid与对应人映射列表
    users = {
        "2093337947": "边大",
        "3598214045": "莫大",
        "2632831661": "罗洄头",
        "3525189939": "自己"
    }
    uid = '2093337947'  # 边大。 如果查多个，可以遍历users列表。但是每个uid下方url中md5参数都不同，也要抓包得到对应md5，写入ini配置文件，再上方新增读取，再传参，较麻烦。
    user = users.get(uid)

    # 各请求url模板
    # 用户专栏
    user_timeline = 'https://xueqiu.com/statuses/original/timeline.json?user_id={}&page=1&count=10&md5__1038={}'
    # 用户发文及回复
    user_text_reply = 'https://xueqiu.com/v4/statuses/user_timeline.json?page=1&user_id={}&md5__1038={}'


    timeline_url = user_timeline.format(uid, timeline_md5)
    timeline = send_xq_get(xq_a_token, u, timeline_url)

    # todo 以下想统一使用snowball_common的api，但报错，未排错
    # timeline = snowball_common.user.get_user_timeline('2093337947',
    # '110279f682e-w9VHusYswqCsm8Saja43knaXmwMyQu9eCqu%2FI9aDddaLka7ICLmsuWSMpxUuMlawRajaLBabBuYLHau4Pa%2Br0sLb0k%2BGtPvaLRaokaUa7gadSaVcH5a0kdYankYi%2Fa40w%2BWZfJLGCaz0LJyvsSlWk%2BLDLHu8xHRaycS8cAukUCXjRowlkKCa')

    # todo 读取本地文件测试
    # with open("专栏响应.json", "r", encoding="utf-8") as f:
    #     print('读取成功')
    #     timeline = json.load(f)
    # print(timeline)
    # 读取本地文件timeline_all.txt比较多次请求是否有新增
    deal_timeline(timeline, 'timeline_all.txt', 'timeline_add.txt', pushplus_token, user)


    text_reply_url = user_text_reply.format(uid, text_reply_md5)
    reply_text = send_xq_get(xq_a_token, u, text_reply_url)
    # # print(reply_text)
    # # todo 本地读取文件进行测试，修改json
    # with open("发文响应.json", "r", encoding="utf-8") as f:
    #     reply_text = json.load(f)
    deal_reply_text(reply_text, 'replyText_all.txt', 'replyText_add.txt', pushplus_token,user)
