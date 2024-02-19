import pprint

from telethon import TelegramClient, events

from pytgcalls import GroupCallFactory

import cfg
# app = TelegramClient('EzhovCalls', regs.ezhov_audio_api_id, regs.ezhov_audio_api_hash).start()
app = TelegramClient('EzhovCalls', cfg.config_data['KEYS']['EZHOV_AUDIO_API_ID'], cfg.config_data['KEYS']['EZHOV_AUDIO_API_HASH']).start()

group_call_factory = GroupCallFactory(app, GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON)
group_call = group_call_factory.get_raw_group_call()
    # get_file_group_call('input.raw')


@app.on(events.NewMessage(pattern='Начинай'))
async def join_handler(event):
    await group_call.start(cfg.FORUM_ID)

app.run_until_disconnected()
