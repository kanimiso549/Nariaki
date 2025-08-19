# config.py（main.pyと同じフォルダに配置）
DISCORD_TOKEN = "BOT_TOKEN"
TARGET_GUILD_IDS = [
    1257965388495323208, # 卵鯖
    876782808847220786, # 堕オナ鯖
]
CHANNEL_IDS = [
    1400485670321000510,  # 卵鯖
    1367045548653416518,  # 堕オナ鯖
]
TARGET_USER_ID = [1401152015551434802]
DMDATA_API_KEY = "AKe.U_rTdjfqTo_ing5W3cKMmwmAeVc1SWQC5_Kpf4FoSKge"

# dmdata (DM-D.S.S)
DMDATA_CLIENT_ID = "CId.vx9wo1iK47YtIeb7-07WD8mdRitJhlM6W0oQk-pmEP-n"
DMDATA_CLIENT_SECRET = "CSt.Nxbbx8ZHAKU2iKMpABuijOFhb28u529dxSSZRBamwVYJ"
DMDATA_TOKEN_URL = "https://manager.dmdata.jp/account/oauth2/v1/token"
DMDATA_WS_URL = "wss://ws.api.dmdata.jp/v2/websocket"
DMDATA_CHANNELS = ["eew.forcast", "telegram.earthquake", "application.jquake"]

# 必要スコープ（契約チャンネル＋socket系）
DMDATA_SCOPE = " ".join([
    "socket.start",
    "socket.list",
    "socket.close",
    "telegram.get.earthquake",
    "telegram.data",
    "eew.get.realtime",
    "eew.get.warning",
    "gd.earthquake",
    "parameter.earthquake",
    "parameter.realtime"
])


# Discord 送信先
TARGET_CHANNEL_IDS = [1400485670321000510, 1367045548653416518]



