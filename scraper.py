import sys
import requests
import json
import pprint
import time
import csv
import constants
import time
if len(sys.argv) != 2:
    print("Must have exactly 1 command line arg of api key. Exiting")
    exit()

api_key = sys.argv[1]
print("API KEY = " + api_key)
pp = pprint.PrettyPrinter(indent=1)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key
}

# DATA WANTED PARAMETERS :
# hot streak X
# winrate X
# champ mastery X
# rank disparity X
# metascore?
# LAST PLAY TIME?! https://developer.riotgames.com/apis#champion-mastery-v4/GET_getChampionMastery >> see by summonerid X
# veteran? X

# Get player list by rank


def get_namelist(tier, rank, page):
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{rank}?page={page}', headers=headers)
    data = json.loads(res.text)
    namelist = [d["summonerName"] for d in data]
    return namelist


def get_summoner_ids(name):
    to_return = dict()
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}', headers=headers)
    data = json.loads(res.text)
    to_return['id'] = data['id']
    to_return['puuid'] = data['puuid']
    return to_return


def get_ranked_stats(sid):
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{sid}', headers=headers)
    data = json.loads(res.text)[0]
    to_return = dict()
    to_return['hot_streak'] = 1.0 if data['hotStreak'] == True else 0.0
    to_return['wr'] = data['wins']/(data['wins'] + data['losses'])
    to_return['rank'] = constants.map_rank(data['tier'], data['rank'])
    to_return['freshBlood'] = data['freshBlood']
    to_return['inactive'] = data['inactive']
    to_return['veteran'] = data['veteran']
    return to_return


def get_champ_stats(sid, cid):
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{sid}', headers=headers)
    data = json.loads(res.text)
    to_return = dict()
    cstats = [x for x in data if x['championId'] == cid]
    if len(cstats) > 0:
        cstats = cstats[0]
        now = time.time() * 1000
        return {'championPoints': cstats['championPoints'], 'lastPlayTime': (now - cstats['lastPlayTime'])/(86400 * 1000)}
    else:
        return {'championPoints': 0, 'lastPlayTime': None}


def get_player_entry(sid):
    rankstats = get_ranked_stats(sid)
    champstats = get_champ_stats(sid, 22)
    to_return = {**rankstats, **champstats}
    return(to_return)


def get_matchlist(puuid, existing_mids):
    res = requests.get(
        f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20', headers=headers)
    data = json.loads(res.text)
    mids = []
    for mid in data:
        if mid not in existing_mids:
            mids.append(mid)

    return mids


def get_participants(match_id):
    res = requests.get(
        f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}', headers=headers)
    data = json.loads(res.text)
    data = data['info']['participants']
    participants = {'win': [], 'lose': []}
    for p in data:
        if p['teamId'] == 100:
            participants['win'].append(p['puuid'])
        else:
            participants['lose'].append(p['puuid'])
    return participants


def get_sid_from_puuid(puuid):
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}', headers=headers)
    data = json.loads(res.text)
    return data['id']


def process_matchdata(mid):
    team_keys = ['win', 'lose']
    summoners = get_participants(mid)
    team_data = None

    # sum stats of all players on winning/losing team
    for team_key in team_keys:
        denoms = {'hot_streak': 0.0, 'wr': 0.0, 'rank': 0.0, 'freshBlood': 0.0,
                  'inactive': 0.0, 'veteran': 0.0, 'chapmionPoints': 0, 'lastPlayTime': None}
        print(denoms)
        for puuid in summoners[team_key]:
            sid = get_sid_from_puuid(puuid)
            if team_data == None:
                team_data = get_player_entry(sid)
            else:
                x = get_player_entry(sid)
                keyname = ""
                try:
                    for k in team_data.keys():
                        keyname = k
                        if x[k] != None:
                            team_data[k] = team_data[k] + x[k]
                            denoms[k] = denoms[k] + 1
                except KeyError:
                    print("lol?")
        print(denoms)
    # get avg


# MAIN
match_ids = []

# populate list with match ids
for i in range(1, 2):
    namelist = get_namelist('GOLD', 'III', i)
    for name in [namelist[0]]:
        ids = get_summoner_ids(name)
        match_ids.extend(get_matchlist(ids['puuid'], match_ids))

for mid in match_ids[0:2]:
    process_matchdata(mid)
# for n in namelist:
# try:
#     process_mdata(name)
# except KeyError:
#     print('lmaoooooo')
#     time.sleep(30)
# else:
#     print('line written')
