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

def printerr(errsrc, e, extra_data=None):
    print(f"EXCEPTION OCCURRED IN {errsrc}: {e}")
    if extra_data != None:
        print(f"\t{extra_data}")


# handling for exceeding rate limit on fx that make riot api calls
def ratelimit_decorator(fx, **kwargs):
    data_obj = None
    try:
        data_obj = fx(**kwargs)
    except Exception as e:
        printerr(e, "RATELIMIT DECORATOR!")
    if type(data_obj) == dict and data_obj.get('status') != None:
        print("******RLDEC:******")
        pp.pprint(data_obj['sma'])
        print("******RLDEC (END):******")

    return data_obj


def get_namelist(**kwargs):  # Get player list by rank. kwargs = tier, rank, page
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{kwargs["tier"]}/{kwargs["rank"]}?page={kwargs["page"]}', headers=headers)
    data = json.loads(res.text)
    try:
        namelist = [d["summonerName"] for d in data]
        return namelist
    except Exception as e:
        printerr('get_namelist', e, data)
        return None


def get_summoner_ids(**kwargs):  # kwargs = name
    to_return = dict()
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{kwargs["name"]}', headers=headers)
    data = json.loads(res.text)
    to_return['id'] = data['id']
    to_return['puuid'] = data['puuid']
    return to_return


def get_ranked_stats(**kwargs):  # kwarg = sid
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{kwargs["sid"]}', headers=headers)
    data = json.loads(res.text)[0]
    to_return = dict()
    to_return['hot_streak'] = 1.0 if data['hotStreak'] == True else 0.0
    to_return['wr'] = data['wins']/(data['wins'] + data['losses'])
    to_return['rank'] = constants.map_rank(data['tier'], data['rank'])
    to_return['freshBlood'] = data['freshBlood']
    to_return['inactive'] = data['inactive']
    to_return['veteran'] = data['veteran']
    return to_return


def get_champ_stats(**kwargs):  # kwargs = sid,cid
    sid = kwargs['sid']
    cid = kwargs['cid']

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


def get_player_entry(**kwargs):  # kwarg = sid
    sid = kwargs['sid']
    rankstats = get_ranked_stats(sid=sid)
    champstats = get_champ_stats(sid=sid, cid=22)  # HARDCODED? WHAT THE FUCK?
    to_return = {**rankstats, **champstats}
    return(to_return)


def get_matchlist(**kwargs):  # kwargs = puuid, existing_mids
    puuid = kwargs['puuid']
    existing_mids = kwargs['existing_mids']
    res = requests.get(
        f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20', headers=headers)
    data = json.loads(res.text)
    mids = []
    for mid in data:
        if mid not in existing_mids:
            mids.append(mid)

    return mids


def get_participants(**kwargs):
    match_id = kwargs['match_id']
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


def get_sid_from_puuid(**kwargs):
    puuid = kwargs['puuid']
    res = requests.get(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}', headers=headers)
    data = json.loads(res.text)
    return data['id']


def process_matchdata(mid):
    team_keys = ['win', 'lose']
    summoners = ratelimit_decorator(get_participants, match_id=mid)
    entry_data = {'win': None, 'lose': None}
    # sum stats of all players on winning/losing team
    for team_key in team_keys:
        # dict to keep track of # entries per key for calculating mean
        denoms = {'hot_streak': 0.0, 'wr': 0.0, 'rank': 0.0, 'freshBlood': 0.0,
                  'inactive': 0.0, 'veteran': 0.0, 'championPoints': 0, 'lastPlayTime': 0}
        for puuid in summoners[team_key]:
            sid = ratelimit_decorator(get_sid_from_puuid, puuid=puuid)
            if entry_data[team_key] == None:
                entry_data[team_key] = ratelimit_decorator(
                    get_player_entry, sid=sid)
            else:
                x = ratelimit_decorator(get_player_entry, sid=sid)
                try:

                    for k in entry_data[team_key].keys():
                        if x[k] != None:
                            # Special case: some fields might have a None entry (e.g. lastplaytime) instead of 0. handle accordingly
                            if entry_data[team_key][k] != None:
                                entry_data[team_key][k] = entry_data[team_key][k] + x[k]
                                denoms[k] = denoms[k] + 1
                            else:
                                entry_data[team_key][k] = None
                except Exception as e:
                    printerr('process_matchdata', e, x)

        # get team avg
        for k in entry_data[team_key].keys():
            if entry_data[team_key][k] != None:
                entry_data[team_key][k] = entry_data[team_key][k] / denoms[k]

    lose_csvrow = {}
    win_csvrow = {}
    # calc pairwise differences for the game
    for k in entry_data['win'].keys():
        win_csvrow[k] = entry_data['win'][k] - entry_data['lose'][k]
        win_csvrow['outcome'] = 1
        lose_csvrow[k] = win_csvrow[k] * -1
        lose_csvrow['outcome'] = 0
    print("WRITING ROWS:")
    pp.pprint(win_csvrow)
    pp.pprint(lose_csvrow)


def main():
    # MAIN
    match_ids = []

    # populate list with match ids
    for i in range(1, 2):
        namelist = ratelimit_decorator(
            get_namelist, tier='GOLD', rank='III', page=i)
        try:
            for name in namelist:
                ids = ratelimit_decorator(get_summoner_ids, name=name)
                match_ids.extend(ratelimit_decorator(get_matchlist,
                                                     puuid=ids['puuid'], existing_mids=match_ids))
        except Exception as e:
            printerr('(main, populate m_id list)', e)

    # use match id list to populate input .csv for ML model
    for mid in match_ids:
        try:
            process_matchdata(mid)
        except Exception as e:
            printerr('(main, process_matchdata loop)', e)


if __name__ == '__main__':
    main()
