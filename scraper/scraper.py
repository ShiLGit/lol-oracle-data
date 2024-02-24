import sys
import requests
import json
import time
from datetime import date
import constants as constants
import csv
import cloudutils

api_key = None 
headers = None

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
    request_flag = True  # flag that causes request to be reattempted on ratelimit exception
    try:
        while request_flag:
            print(f"request to {url}")
            res = requests.get(url, headers=headers)
            data = json.loads(res.text)
            if type(data) == dict and data.get('status') != None and data['status'].get('status_code') == 429:
                print("RATELIMIT EXCEEDED: Sleeping 15s.")
                time.sleep(15)
                print("RESUMING!")
            else:
                request_flag = False
    except Exception as e:
        printerr(e, "REQUEST DECORATOR")

    return data


def get_namelist(tier, rank, page):
    try:
        data = request_decorator(
            f'https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{rank}?page={page}')
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
    data = None
    try:
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
    except Exception as e:
        printerr("get_ranked_stats", e)
        print(f"\tRESPONSE DATA = {data}")


# stat = lastPlayTime from req obj of get_champ_stats. for None handling, just return max lastplaytime of 90 days
def compute_lastplaytime(stat):
    sec_per_day = 86400
    now = time.time()
    if stat == None:
        return sec_per_day * 90

    lastPlayTime = (now - stat)/sec_per_day
    return min(90 * sec_per_day, lastPlayTime)


def get_champ_stats(puuid, cid):
    data = None
    try:
        data = request_decorator(
            f'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{cid}')
        
        if 'status' in data.keys() and data.status['status_code'] == 404: # req will return 404 if player hasn't played champ of cid
            #TODO None?? does that mess up the data? What about encoding them manually?
            #TODO encode last playtime (0 for never played, 1 for >= 6 mos... go figure?), compare train on encode vs non encode
            return {'championPoints': 0, 'lastPlayTime': None} 

        return {'championPoints': data['championPoints'], 'lastPlayTime': compute_lastplaytime(data['lastPlayTime'])}

    except Exception as e:
        printerr("get_champ_stats", e)
        print(f"\tRESPONSE DATA = {data}")


def get_player_entry(sid, cid, puuid):
    rankstats = get_ranked_stats(sid)
    champstats = get_champ_stats(puuid, cid)
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
        participant = {'puuid': p['puuid'], 'cid': p['championId']}
        if p['teamId'] == 100:
            participants['win'].append(participant)
        else:
            participants['lose'].append(participant)
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
        # dict to keep track of # entries per key for calculating mean >> one player has DNE entry? adjust accordingly
        denoms = {'hot_streak': 0.0, 'wr': 0.0, 'rank': 0.0, 'freshBlood': 0.0,
                  'inactive': 0.0, 'veteran': 0.0, 'championPoints': 0, 'lastPlayTime': 0}

        for summoner in summoners[team_key]:
            puuid = summoner['puuid']
            sid = get_sid_from_puuid(puuid=puuid)
            player_entry = get_player_entry(sid=sid, cid=summoner['cid'], puuid = puuid)
            if entry_data[team_key] == None:
                entry_data[team_key] = player_entry

            try:
                for k in entry_data[team_key].keys():
                    if player_entry[k] != None:
                        # Special case: some fields might have a None entry (e.g. lastplaytime) instead of 0. handle accordingly
                        if entry_data[team_key][k] != None:
                            entry_data[team_key][k] = entry_data[team_key][k] + \
                                player_entry[k]
                            denoms[k] = denoms[k] + 1
                        else:
                            entry_data[team_key][k] = None

            except Exception as e:
                printerr('process_matchdata', e, player_entry)

        # get team avg
        for k in entry_data[team_key].keys():
            print(denoms)
            if entry_data[team_key][k] != None:
                if denoms[k] == 0:
                    print(f"denom {k} computed to be 0!?!")
                entry_data[team_key][k] = entry_data[team_key][k] / denoms[k]

    lose_csvrow = {'m_id': mid}
    win_csvrow =  {'m_id': mid}

    # calc pairwise differences for the game
    for k in entry_data['win'].keys():
        win_csvrow[k] = entry_data['win'][k] - entry_data['lose'][k]
        win_csvrow['outcome'] = 1
        lose_csvrow[k] = win_csvrow[k] * -1
        lose_csvrow['outcome'] = 0
    print("COMPUTED ROWS:")
    print(win_csvrow)
    print(lose_csvrow)
    return [win_csvrow, lose_csvrow]

def get_matchlist_by_rank(tier, rank):
    match_ids = []

    # populate list with match ids
    print("***********************************************\nPOPULATING MATCH LIST\n******************************************\n")
    for i in range(1, 2): #DEBUG 
        try:
            namelist = get_namelist(tier=tier, rank=rank, page=i)
            for name in namelist:
                ids = get_summoner_ids(name=name)
                match_ids.extend(get_matchlist(
                    puuid=ids['puuid'], existing_mids=match_ids))
                break  # REMOVE THIS BREKA >> ADDED JUST TO REDUCE # COLLECTED MATCHIDS BECAUSE IT TAKES TOO LONG DURING DEBUG

        except Exception as e:
            printerr('(main, populate m_id list)', e)
    return match_ids

def get_fname(tier, rank, chunk_num = None):
    date_str = date.today().strftime("%d-%m-%Y")
    if chunk_num:
        return f"{tier}-{rank}_{date_str}_{chunk_num}"
    else: 
        return f"{tier}-{rank}_{date_str}"

def main(apiKey, tier='PLATINUM', rank='II', local = False):
    global headers 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": apiKey
    }

    match_ids = get_matchlist_by_rank(tier, rank)
    chunk_num = 0
    filepath = f"../data/{get_fname(tier, rank)}.csv"
    csv_fptr = open(filepath, 'w')


    # use match id list to populate input .csv for ML model
    writer = csv.DictWriter(csv_fptr, fieldnames=['hot_streak', 'wr', 'rank', 'freshBlood',
                                                    'inactive', 'veteran', 'championPoints', 'lastPlayTime', 'outcome', 'm_id']) # + m_id
    writer.writeheader()
    row_count = 0
    for mid in match_ids:
        print(
            f"***********************************************\nPOPULATING MATCH ID {mid}\n******************************************\n")
        try:
            matchrows = process_matchdata(mid)
            for row in matchrows:
                writer.writerow(row)
                print("Writing rows..")
                csv_fptr.flush()

            # do cloud util SHIT: upload contents of working file and then clear it to be populated for next chunk upload
            if row_count % 2 == 0 and not local: 
                row_count = 0 
                cloudutils.upload(filepath, get_fname(tier, rank, chunk_num))
                print(f"UPLOADING CHUNK {chunk_num}: {get_fname(tier, rank, chunk_num)}") 
                chunk_num = chunk_num + 1
                csv_fptr.close() 
                csv_fptr = open(filepath, 'w')

            row_count = row_count + 1
        except Exception as e:
            printerr('(main, process_matchdata loop)', e)

    csv_fptr.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Must include api key in run command (simplest case: py scraper.py <api key>). Exiting")
        exit()


    api_key = sys.argv[1]
    if len(sys.argv) == 4:  # py scraper.py <API_KEY> <rank> <tier>
        main(apiKey=api_key, tier=sys.argv[2].upper(), rank=sys.argv[3].upper(), local = True)
    else:
        main(apiKey=api_key)
