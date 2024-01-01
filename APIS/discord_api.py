import requests


class DiscordBot(object):
    def __init__(self):
        self.url_webhook = "https://discord.com/api/webhooks/1191359298157154374/IG3UrJprUum9wGcXwQvpQH3ZFIVqeukTcs8CfMTWJQzrrEQFeBbRyxybamGVAstIKuUC"

    def waves_alert(self, message: str):
        data = {"content": message.encode("utf-8")}
        r = requests.post(url=self.url_webhook, data=data)
        return
