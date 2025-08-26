import configparser
import logging
import os
import asyncio
import random
from typing import Dict, Optional, Union
from collections import defaultdict

import telethon.events
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPhoto, InputChannel, PeerChat

# 全局变量
clients_pool = {}  # {client: cloned_user_id or None}
client_locks = {}  # {client: asyncio.Lock}
sender_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
message_id_mapping = {}
cloned_users = set()
frozen_clients = set()  # 冻结账号集合

logging.getLogger('telethon').setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    PROXY = None
    SOURCE_GROUPS = []
    TARGET_GROUP: Union[PeerChat, InputChannel]
    BLACK_LIST = set()
    KEY_WORDS = set()
    REPLACEMENTS = {}
    API_ID = None
    API_HASH = None

async def load_existing_sessions(choice: str) -> None:
    for filename in os.listdir('sessions'):
        if filename.endswith('.session'):
            session_name = filename.replace('.session', '')
            logger.info(f"正在加载 session: {session_name}")
            client = TelegramClient(f"sessions/{session_name}", Config.API_ID, Config.API_HASH, proxy=Config.PROXY)
            await client.connect()
            if await client.is_user_authorized():
                logger.info(f"加载成功 session: {session_name}")
                if choice == '3':
                    await delete_profile_photos(client)
                elif choice == '4':
                    await check_and_join_target(client)
                clients_pool[client] = None
                client_locks[client] = asyncio.Lock()
            else:
                logger.warning(f"未授权 session: {session_name}")
                await client.disconnect()


def load_config() -> None:
    config_path = "setting/config.ini"
    default_content = """[telegram]
api_id = 3642180
api_hash = 636c15dbfe0b01f6fab88600d62667d0
source_group = https://t.me/amlhcgj
target_group = https://t.me/amlhcgj

[proxy]
is_enabled = false
host = 127.0.0.1
port = 7890
type = socks5

[blacklist]
user_ids = 123,12345
keywords = 广告，推广

[replacements]
a = b
你好 = 我好
"""

    os.makedirs("setting", exist_ok=True)
    os.makedirs('sessions', exist_ok=True)
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_content)
            logger.info(f"已初始化配置文件: {config_path}")

    config = configparser.ConfigParser()
    try:
        config.read(config_path, encoding="utf-8-sig")

        Config.API_HASH = config.get("telegram", "api_hash")
        Config.API_ID = config.getint("telegram", "api_id")

        raw_source_gps = config.get("telegram", "source_group")
        Config.SOURCE_GROUPS = [source_gp for source_gp in raw_source_gps.split(",") if source_gp.strip()]
        Config.TARGET_GROUP = config.get("telegram", "target_group")

        if config.getboolean("proxy", "is_enabled"):
            host = config.get("proxy", "host")
            port = config.getint("proxy", "port")
            proxy_type = config.get("proxy", "type")
            Config.PROXY = (proxy_type, host, port)

        # 黑名单
        blacklist_str = config.get("blacklist", "user_ids", fallback="")
        keywords_str = config.get("blacklist", "keywords", fallback="")
        Config.BLACK_LIST.update(int(uid) for uid in blacklist_str.split(",") if uid.strip().isdigit())
        Config.KEY_WORDS.update(keyword.strip() for keyword in keywords_str.split(",") if keyword.strip())

        # 替换词
        if config.has_section("replacements"):
            Config.REPLACEMENTS.update(dict(config.items("replacements")))

        logger.info(f"成功加载配置文件: {config_path}")
    except Exception as e:
        logger.error(f"配置加载失败: {e}")


async def delete_profile_photos(client: TelegramClient) -> None:
    try:
        me = await client.get_me()
        photos = await client.get_profile_photos(me.id)
        for photo in photos:
            await client(DeletePhotosRequest([InputPhoto(
                id=photo.id,
                access_hash=photo.access_hash,
                file_reference=photo.file_reference
            )]))
        logger.info(f"[{me.phone}] 清空历史头像成功")
    except Exception as e:
        logger.error(e)


async def check_and_join_target(client: TelegramClient) -> None:
    try:
        await client(JoinChannelRequest(Config.TARGET_GROUP))
        me = await client.get_me()
        logger.info(f"[{me.phone}] 加入目标群组成功")
    except Exception as e:
        if "FROZEN_METHOD_INVALID" in str(e):
            await cleanup_frozen_client(client)
            logger.error(f"克隆账号加入目标群组失败: {e}")
        else:
            logger.info(e)


async def check_and_join_source(client: TelegramClient, group: InputChannel) -> None:
    try:
        await client(JoinChannelRequest(group))
        logger.info("监听账号加入源群组成功")
    except Exception as e:
        if "FROZEN_METHOD_INVALID" in str(e):
            await cleanup_frozen_client(client)
            logger.error(f"监听账号加入源群组失败: {e}")


async def clone_and_forward_message(event, monitor_client: TelegramClient) -> None:
    sender = await event.get_sender()
    if not sender or sender.bot:
        return

    sender_id = sender.id
    lock = sender_locks[sender_id]
    async with lock:
        if sender_id in Config.BLACK_LIST:
            return

        if any(keyword in (event.message.text or "") for keyword in Config.KEY_WORDS):
            return

        # 已分配过的 client
        for client, cloned_user in list(clients_pool.items()):
            if cloned_user == sender_id:
                if client in frozen_clients:
                    continue
                lock = client_locks[client]
                async with lock:
                    try:
                        await asyncio.sleep(random.uniform(1, 5.5))
                        me = await client.get_me()
                        await forward_message_as(client, event, monitor_client)
                        logger.info(f"[{me.phone}] 转发 {sender_id} 的新消息")
                    except Exception as e:
                        if "FROZEN_METHOD_INVALID" in str(e):
                            await cleanup_frozen_client(client, sender_id)
                        logger.info(f"转发失败（已克隆用户）: {e}")
                return

        # 未分配的 client
        for client, cloned_user in list(clients_pool.items()):
            if cloned_user is None and client not in frozen_clients:
                lock = client_locks[client]
                async with lock:
                    try:
                        await monitor_client.get_input_entity(sender_id)
                        me = await client.get_me()
                        logger.info(f"[{me.phone}] 正在克隆新用户: {sender_id}")

                        # 再次检查是否已分配
                        if clients_pool[client] is not None:
                            continue

                        # 设置昵称
                        try:
                            await client(UpdateProfileRequest(
                                first_name=sender.first_name or " ",
                                last_name=sender.last_name or "",
                            ))
                            logger.info(f"[{me.phone}] 设置昵称成功")
                        except Exception as e:
                            if "FROZEN_METHOD_INVALID" in str(e):
                                await cleanup_frozen_client(client, sender_id)
                                return
                            logger.error(f"设置昵称失败: {e}")

                        # 设置头像
                        try:
                            photos = await monitor_client.get_profile_photos(sender, limit=1)
                            if photos:
                                profile_path = await monitor_client.download_media(photos[0])
                                if profile_path and os.path.exists(profile_path):
                                    uploaded = await client.upload_file(file=profile_path)
                                    if photos[0].video_sizes:
                                        await client(UploadProfilePhotoRequest(video=uploaded))
                                    else:
                                        await client(UploadProfilePhotoRequest(file=uploaded))
                                    os.remove(profile_path)
                                    logger.info(f"[{me.phone}] 设置头像成功")
                        except Exception as e:
                            if "FROZEN_METHOD_INVALID" in str(e):
                                await cleanup_frozen_client(client, sender_id)
                                return
                            logger.error(f"设置头像失败: {e}")

                        # 转发消息
                        await forward_message_as(client, event, monitor_client)

                        clients_pool[client] = sender_id
                        cloned_users.add(sender_id)
                        logger.info(f"[{me.phone}] 完成新用户克隆: {sender_id}")
                    except Exception as e:
                        if "FROZEN_METHOD_INVALID" in str(e):
                            await cleanup_frozen_client(client, sender_id)
                        logger.warning(f"克隆失败: {e}")
                return

        logger.info("无可用账号进行克隆")


async def forward_message_as(client: TelegramClient, event: telethon.events.NewMessage.Event,
                             monitor_client: TelegramClient) -> None:
    message = event.message
    text = apply_replacements(message.text or "")
    target_group = Config.TARGET_GROUP

    try:
        if message.is_reply:
            reply = await event.get_reply_message()
            if not reply:
                logger.warning("无法获取被回复消息")
                return

            reply_to_msg_id = message_id_mapping.get(reply.id)
            if reply_to_msg_id is None:
                logger.info("没有找到对应的克隆账号消息，跳过回复")
                return

            if message.media:
                file_path = await monitor_client.download_media(message)
                original_attributes = getattr(message.media, 'document', None)
                sent_reply = await client.send_file(
                    target_group,
                    file_path,
                    attributes=getattr(original_attributes, 'attributes', None),
                    reply_to=reply_to_msg_id,
                    caption=text
                )
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            else:
                sent_reply = await client.send_message(target_group, text, reply_to=reply_to_msg_id)

            message_id_mapping[message.id] = sent_reply.id

        else:
            if message.media:
                file_path = await monitor_client.download_media(message)
                original_attributes = getattr(message.media, 'document', None)
                sent = await client.send_file(
                    target_group,
                    file_path,
                    attributes=getattr(original_attributes, 'attributes', None),
                    caption=text
                )
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            else:
                sent = await client.send_message(target_group, text)

            message_id_mapping[message.id] = sent.id

    except Exception as e:
        if "FROZEN_METHOD_INVALID" in str(e):
            await cleanup_frozen_client(client)
        logger.error(f"发送消息失败: {e}")


def apply_replacements(text: str) -> str:
    if not text:
        return text
    for k, v in Config.REPLACEMENTS.items():
        text = text.replace(k, v)
    return text


async def cleanup_frozen_client(client: TelegramClient, sender_id: Optional[int] = None) -> None:
    try:
        me = await client.get_me()
        phone = me.phone
        logger.warning(f"[{phone}][FROZEN] 账号被冻结，已移除")
        frozen_clients.add(client)

        await client.disconnect()
        clients_pool.pop(client, None)
        client_locks.pop(client, None)

        if sender_id:
            cloned_users.discard(sender_id)
    except Exception as e:
        logger.warning(f"清理被冻结账号失败: {e}")


async def start_monitor() -> None:
    session_file = 'monitor'
    monitor_client = TelegramClient(session_file, Config.API_ID, Config.API_HASH, proxy=Config.PROXY)
    await monitor_client.connect()

    if not await monitor_client.is_user_authorized():
        phone = input('请输入监听账号手机号: ')
        y = await monitor_client.send_code_request(phone)
        code = input('输入验证码: ')
        try:
            await monitor_client.sign_in(phone, code, phone_code_hash=y.phone_code_hash)
        except SessionPasswordNeededError:
            password = input("请输入2FA 密码: ")
            await monitor_client.sign_in(password=password)

    me = await monitor_client.get_me()
    logger.info(f"监听账号登录成功: {me.phone}")

    for group in Config.SOURCE_GROUPS:
        await check_and_join_source(monitor_client, group)

    logger.info("开始监听消息")

    @monitor_client.on(events.NewMessage(chats=Config.SOURCE_GROUPS))
    async def handler(event: telethon.events.NewMessage.Event):
        try:
            await clone_and_forward_message(event, monitor_client)
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    await monitor_client.run_until_disconnected()