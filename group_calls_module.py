from telethon import TelegramClient, events

from pytgcalls import GroupCallFactory

import regs

app = TelegramClient('EzhovAudio', regs.ezhov_audio_api_id, regs.ezhov_audio_api_hash).start()
group_call_factory = GroupCallFactory(app, GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON)
group_call = group_call_factory.get_file_group_call('input.raw')


@app.on(events.NewMessage(pattern='Hello'))
async def join_handler(event):
    await group_call.start(regs.zhenya_forum_id)

app.run_until_disconnected()
