import sys
import requests

if len(sys.argv) != 2:
    print("Must have exactly 1 command line arg of api key. Exiting")
    exit()

api_key = sys.argv[1]
print("API KEY = " + api_key)
# Data scraper used to procure dataset (data.csv). API key is expired so it doesn't work
# Match KDR was mistakenly scraped, never used because it's an endgame stat rather than a pregame stat
headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key
}

