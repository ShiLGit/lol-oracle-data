import sys
import requests
import json
import pprint
import time
import csv
import constants
import time
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
# LAST PLAY TIME?! https://developer.riotgames.com/apis#champion-mastery-v4/GET_getChampionMastery >> see by summonerid X. COMPUTED as # days since last playing cur champ
# veteran? X


def printerr(errsrc, e, extra_data=None):
    print(f"EXCEPTION OCCURRED IN {errsrc}: {e}")
    if extra_data != None:
        print(f"\t{extra_data}")


def request_decorator(url):
    data = None
    try:
        res = requests.get(url, headers=headers)
        data = json.loads(res.text)
        if type(data) == dict and data.get('status') != None:
            if data['status'].get('status_code') == 429:
                print("RATELIMIT EXCEEDED: Sleeping 30s.")
                time.sleep(30)
                print("RESUMING!")
    except Exception as e:
        printerr(e, "REQUEST DECORATOR")

    return data


def get_namelist(tier, rank, page):
    data = request_decorator(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{rank}?page={page}')

    try:
        namelist = [d["summonerName"] for d in data]
        return namelist
    except Exception as e:
        printerr('get_namelist', e, data)
        return None


def get_summoner_ids(name):
    to_return = dict()
    data = request_decorator(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}')

    to_return['id'] = data['id']
    to_return['puuid'] = data['puuid']
    return to_return


def get_ranked_stats(sid):
    data = request_decorator(
        f'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{sid}')[0]
    to_return = dict()
    to_return['hot_streak'] = 1.0 if data['hotStreak'] == True else 0.0
    to_return['wr'] = data['wins']/(data['wins'] + data['losses'])
    to_return['rank'] = constants.map_rank(data['tier'], data['rank'])
    to_return['freshBlood'] = data['freshBlood']
    to_return['inactive'] = data['inactive']
    to_return['veteran'] = data['veteran']
    return to_return


def get_champ_stats(sid, cid):
    data = request_decorator(
        f'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{sid}')

    cstats = [x for x in data if x['championId'] == cid]
    if len(cstats) > 0:
        cstats = cstats[0]
        now = time.time() * 1000
        return {'championPoints': cstats['championPoints'], 'lastPlayTime': (now - cstats['lastPlayTime'])/(86400 * 1000)}
    else:
        return {'championPoints': 0, 'lastPlayTime': None}


def get_player_entry(sid):
    rankstats = get_ranked_stats(sid)
    champstats = get_champ_stats(sid, 22)  # HARDCODED? WHAT THE FUCK?
    to_return = {**rankstats, **champstats}
    return(to_return)


def get_matchlist(puuid, existing_mids):
    data = request_decorator(
        f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&start=0&count=20')

    mids = []
    for mid in data:
        if mid not in existing_mids:
            mids.append(mid)

    return mids


def get_participants(match_id):
    data = request_decorator(
        f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}')

    data = data['info']['participants']
    participants = {'win': [], 'lose': []}
    for p in data:
        if p['teamId'] == 100:
            participants['win'].append(p['puuid'])
        else:
            participants['lose'].append(p['puuid'])
    return participants


def get_sid_from_puuid(puuid):
    data = request_decorator(
        f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}')

    return data['id']


def process_matchdata(mid):
    team_keys = ['win', 'lose']
    summoners = get_participants(match_id=mid)
    entry_data = {'win': None, 'lose': None}
    # sum stats of all players on winning/losing team
    for team_key in team_keys:
        # dict to keep track of # entries per key for calculating mean
        denoms = {'hot_streak': 0.0, 'wr': 0.0, 'rank': 0.0, 'freshBlood': 0.0,
                  'inactive': 0.0, 'veteran': 0.0, 'championPoints': 0, 'lastPlayTime': 0}

        for puuid in summoners[team_key]:
            sid = get_sid_from_puuid(puuid=puuid)
            if entry_data[team_key] == None:

                entry_data[team_key] = get_player_entry(sid=sid)

            else:
                x = get_player_entry(sid=sid)
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
                if denoms[k] == 0:
                    print("WHAT THE FUCK?!")
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
    with open('test.csv') as fp:
        fp.writeline(win_csvrow)
        fp.writeline(lose_csvrow)


def main():
    # MAIN
    match_ids = []

    # populate list with match ids
    print("***********************************************\nPOPULATING MATCH LIST\n******************************************\n")
    for i in range(1, 2):
        namelist = get_namelist(tier='GOLD', rank='III', page=i)
        try:
            for name in namelist:
                ids = get_summoner_ids(name=name)
                match_ids.extend(get_matchlist(
                    puuid=ids['puuid'], existing_mids=match_ids))
                break  # REMOVE THIS BREKA >> ADDED JUST TO REDUCE # COLLECTED MATCHIDS BECAUSE IT TAKES TOO LONG DURING DEBUG

        except Exception as e:
            printerr('(main, populate m_id list)', e)

    # use match id list to populate input .csv for ML model
    for mid in match_ids:
        print(
            f"***********************************************\nPOPULATING MATCH ID {mid}\n******************************************\n")
        try:
            process_matchdata(mid)
        except Exception as e:
            printerr('(main, process_matchdata loop)', e)


if __name__ == '__main__':
    main()
