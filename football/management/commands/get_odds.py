from django.core.management.base import BaseCommand, CommandError
from football.models import Team, Division

import datetime
import json
import urllib
import urllib.request
import urllib.error
import sys

class Command(BaseCommand):
    session_token = 'HqQvWUj4lbYtwWCfVCYSgq5CVI0Vw3oj1Dg+rxf1OlI='
    help = 'Get the latest odds from BetFair'
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = { 'X-Application' : 'SMDsyAVkt1mi6WVg', 'X-Authentication' : session_token, 'content-type' : 'application/json' }

    def callAping(self, jsonrpc_req):
        try:
            req = urllib.request.Request(self.url, jsonrpc_req.encode('utf-8'), self.headers)
            response = urllib.request.urlopen(req)
            jsonResponse = response.read()
            return jsonResponse.decode('utf-8')
        except urllib.error.URLError as e:
            print (e.reason)
            print ('Oops no service available at ' + str(self.url))
            exit()
        except urllib.error.HTTPError:
            print ('Oops not a valid operation from the service ' + str(self.url))
            exit()


    def getEventTypes(self):
        event_type_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEventTypes", "params": {"filter":{ }}, "id": 1}'
        print ('Calling listEventTypes to get event Type ID')
        eventTypesResponse = self.callAping(event_type_req)
        eventTypeLoads = json.loads(eventTypesResponse)
        """
        print(eventTypeLoads)
        """
        try:
            eventTypeResults = eventTypeLoads['result']
            return eventTypeResults
        except:
            print ('Exception from API-NG' + str(eventTypeLoads['error']))
            exit()


    def getEventTypeIDForEventTypeName(self, eventTypesResult, requestedEventTypeName):
        if(eventTypesResult is not None):
            for event in eventTypesResult:
                eventTypeName = event['eventType']['name']
                if(eventTypeName == requestedEventTypeName):
                    return event['eventType']['id']
        else:
            print('Oops there is an issue with the input')
            exit()

    def getCompetitionIDForCompetitionName(self, competitionResults, requestedCompetitionName):
        if (competitionResults is not None):
            for competition in competitionResults:
                competitionName = competition['competition']['name']
                if (competitionName == requestedCompetitionName):
                    return competition['competition']['id']
        else:
            print ('Oops there is an issue with the input')
            exit()


    def getCompetitionsForEventTypeID(self, eventTypeID):
        competitions_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCompetitions", "params": {"filter":{ "eventTypeIds" : ['+eventTypeID+'], "marketCountries":["GB"]  }}, "id": 1}'
        competitionsResponse = self.callAping(competitions_req)
        competitionLoads = json.loads(competitionsResponse)
        """
        print(competitionLoads)
        """
        try:
            competitionResults = competitionLoads['result']
            return competitionResults
        except:
            print ('Exception from API-NG' + str(competitionLoads['error']))
            exit()


    def getEventID(self, competitionID, home_team, away_team):
        events_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEvents", "params": {"filter":{ "competitionIds" : ['+competitionID+'], "textQuery" : "'+home_team+' '+away_team+'"  }}, "id": 1}'
        eventsResponse = self.callAping(events_req)
        eventLoads = json.loads(eventsResponse)
        """
        print(eventLoads)
        """
        try:
            eventResults = eventLoads['result']
            return eventResults[0]['event']['id']
        except:
            print ('Exception from API-NG' + str(eventLoads['error']))
            exit()


    def getMarketID(self, eventID):
        market_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", "params": {"filter":{ "eventIds" : ['+eventID+'], "marketTypeCodes" : ["MATCH_ODDS"] }, "marketProjection" : ["RUNNER_DESCRIPTION"], "maxResults":"10" }, "id": 1}'
        marketResponse = self.callAping(market_req)
        marketLoads = json.loads(marketResponse)
        """
        print(eventLoads)
        """
        try:
            marketResults = marketLoads['result']
            return marketResults[0]['marketId'], marketResults[0]['runners']
        except:
            print ('Exception from API-NG' + str(marketLoads['error']))
            exit()

    def getMarketBook(self, marketID):
        """
        MarketIDs
        """
        market_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds" : ['+str(marketID)+'] }, "id": 1}'
        marketResponse = self.callAping(market_req)
        marketLoads = json.loads(marketResponse)
        """
        print(eventLoads)
        """
        try:
            marketResults = marketLoads['result']
            return marketResults
        except:
            print ('Exception from API-NG' + str(marketLoads['error']))
            exit()

    def handle(self, *args, **options):

        eventTypesResult = self.getEventTypes()
        soccerEventTypeID = self.getEventTypeIDForEventTypeName(eventTypesResult, 'Soccer')

        #print ('EventType Id for Soccer is :' + str(soccerEventTypeID))

        soccerCompetitions = self.getCompetitionsForEventTypeID(soccerEventTypeID)
        premierLeagueID = self.getCompetitionIDForCompetitionName(soccerCompetitions, 'English Premier League')

        #print ('Competition Id for English Premier League is :' + str(premierLeagueID))

        eventID = self.getEventID(premierLeagueID, "Arsenal", "Hull")

        #print ('Event ID :' + str(eventID))

        marketID, runners = self.getMarketID(eventID)

        #print ('Market ID : ' + str(marketID))

        prices = {}
        for selection in runners:
            prices[selection['selectionId']] = {}
            prices[selection['selectionId']] = { 'name' : selection['runnerName'] }


        marketBook = self.getMarketBook(marketID)

        for selection in marketBook[0]['runners']:
            prices[selection['selectionId']].update( { 'odds' : selection['lastPriceTraded'] })
        #print ('Market Book: ' + str(marketBook))

        for k,v in prices.items():
            print("{}: {}".format(v['name'], v['odds']))
