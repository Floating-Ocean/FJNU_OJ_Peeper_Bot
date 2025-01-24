from nonebot import on_command
from nonebot.rule import to_me
from src.core.constants import Constants
from nonebot_plugin_saa import MessageFactory, AggregatedMessageFactory


ping = on_command("活着吗",rule=to_me(),aliases={'死了吗','似了吗','ping'},priority=0,block=True)

@ping.handle()
async def handle_ping():
    await MessageFactory("你猜呢").finish()

swear = on_command("傻逼",rule=to_me(),aliases={'智障','制杖','SB','sb','脑瘫','nt'},priority=100,block=True)

@swear.handle()
async def handle_swear():
    await MessageFactory("你干嘛害哎呦").finish()

help = on_command("help",rule=to_me(),aliases={'帮助'},priority=0,block=True)
@help.handle()
async def handle_help():
    await AggregatedMessageFactory(MessageFactory(Constants.merged_help_content)).finish()

