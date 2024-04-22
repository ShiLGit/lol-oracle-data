import functions_framework
import scraper
import constants

# REQUEST TEMPLATE: 
# {
#   "api_key": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
#   "rank": "GOLD",
#   "division": "II"
# }
def validate_request(request_json): 
    if not request_json: 
       return {"isValid": False, "msg": "Request is null!"}
    if "api_key" not in request_json: 
       return {"isValid": False, "msg": "Missing 'api_key' in request body"}
        # TODO: else: validate api key by sending test request 
    if "rank" not in request_json: 
       return {"isValid": False, "msg": "Missing 'rank' in request body"}
    elif request_json['rank'] not in constants.rank_map.keys():
        return {"isValid": False, "msg": "Invalid rank"}
    if "division" not in request_json:
       return {"isValid": False, "msg": "Missing 'division' in request body"}
    elif request_json['division'] not in constants.div_map.keys():
       return {"isValid": False, "msg": "Invalid division"}
        
    

@functions_framework.http
def process_request(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)

    validate_results = validate_request(request_json)
    if validate_results["isValid"] == False:
       return validate_results 
       
    api_key = request_json["api_key"]
    rank = request_json["rank"]
    div = request_json["division"]

    return scraper.main(apiKey = api_key, tier = rank, rank = div, local = False)


  

