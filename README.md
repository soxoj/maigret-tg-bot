# Maigret Telegram bot

Simple telegram bot to run your own [Maigret search](https://github.com/soxoj/maigret) with a couple of clicks!

Official bot: [@maigret_osint_bot](http://t.me/maigret_osint_bot)

## Requirements

- Python 3.6+ and pip is required.
- `pip3 install -r requirements.txt`
- [Register Telegram application](https://core.telegram.org/api/obtaining_api_id) to get API_ID and API_HASH.
- [Create a new bot](https://core.telegram.org/bots#6-botfather), get a token and use it on first script launch. 

## Using

```shell
export API_ID=<your api id>
export API_HASH=<your api hash>
python3 bot.py
```

That's all! Send a username to the created bot to start Maigret search.
