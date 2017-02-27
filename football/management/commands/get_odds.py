import datetime
import json
import urllib
import urllib.request
import urllib.error
import sys

from django.core.management.base import BaseCommand, CommandError

from football.models import Team, Match, Odds, Division


class Command(BaseCommand):
    help = 'Get the latest odds from BetFair'
    session_token = 'dD1g4jFRE82SbHBdKqxLA0wRvkHbb+JFTb5HwqCl6/Y='
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    headers = {
            'X-Application' : 'SMDsyAVkt1mi6WVg',
            'X-Authentication' : session_token,
            'content-type' : 'application/json' }

    def call_api_ng(self, jsonrpc_req):
        try:
            req = urllib.request.Request(
                    self.url, jsonrpc_req.encode('utf-8'), self.headers)
            response = urllib.request.urlopen(req)
            json_response = response.read()
            return json_response.decode('utf-8')
        except urllib.error.URLError as e:
            self.stdout.write(self.style.ERROR(e.reason))
            raise CommandError(
                'Oops no service available at ' + str(self.url))
        except urllib.error.HTTPError:
            raise CommandError(
                'Oops not a valid operation from the service '\
                + str(self.url))

    def get_event_types(self):
        event_type_req = '{"jsonrpc": "2.0",'\
                '"method": "SportsAPING/v1.0/listEventTypes",'\
                '"params": {"filter":{ }}, "id": 1}'
        event_types_response = self.call_api_ng(event_type_req)
        event_types_loads = json.loads(event_types_response)
        try:
            event_type_results = event_types_loads['result']
            return event_type_results
        except:
            raise CommandError(
                'Exception from API-NG'\
                + str(event_types_loads['error']))

    def get_event_type_id(self, event_types, requestedEventTypeName):
        if(event_types is not None):
            for event in event_types:
                eventTypeName = event['eventType']['name']
                if(eventTypeName == requestedEventTypeName):
                    return event['eventType']['id']
        else:
            raise CommandError('Oops there is an issue with the input')

    def get_competition_id(
            self, competition_results, competition_name):
        if (competition_results is not None):
            for competition in competition_results:
                name = competition['competition']['name']
                if (name == competition_name):
                    return competition['competition']['id']
        else:
            raise CommandError('Oops there is an issue with the input')

    def get_competitions(self, eventTypeID):
        competitions_req = '{"jsonrpc": "2.0", '\
                '"method": "SportsAPING/v1.0/listCompetitions",'\
                '"params": {"filter":{ '\
                '"eventTypeIds" : ["'+str(eventTypeID)+'"],'\
                '"marketCountries":["GB"]  }}, "id": 1}'
        competitions_response = self.call_api_ng(competitions_req)
        competition_loads = json.loads(competitions_response)
        try:
            competition_results = competition_loads['result']
            return competition_results
        except:
            raise CommandError(
                'Exception from API-NG'\
                + str(competition_loads['error']))

    def get_event_id(self, competition_id, home_team, away_team):
        events_req = '{"jsonrpc": "2.0",'\
                '"method": "SportsAPING/v1.0/listEvents",'\
                '"params": {"filter":'\
                '{ "competitionIds" : ["'+str(competition_id)+'"],'\
                '"textQuery" : "'+home_team+' '+away_team+'"  }},'\
                '"id": 1}'
        events_response = self.call_api_ng(events_req)
        event_loads = json.loads(events_response)
        try:
            event_results = event_loads['result']
            return event_results[0]['event']['id']
        except:
            raise CommandError(
                'Exception from API-NG' + str(event_loads['error']))

    def get_market_id(self, event_id):
        market_req = '{"jsonrpc": "2.0", '\
                '"method": "SportsAPING/v1.0/listMarketCatalogue",'\
                '"params": {"filter":{ "eventIds" : ["'+str(event_id)+'"],'\
                '"marketTypeCodes": ["MATCH_ODDS", "OVER_UNDER_25"] },'\
                '"marketProjection" : ["RUNNER_DESCRIPTION"],'\
                '"maxResults":"10" }, "id": 1}'
        market_response = self.call_api_ng(market_req)
        market_loads = json.loads(market_response)
        try:
            market_results = market_loads['result']
            return market_results[0]['marketId'], market_results
        except:
            raise CommandError(
                'Exception from API-NG' + str(market_loads['error']))

    def get_market_book(self, market_id):
        market_req = '{"jsonrpc": "2.0",'\
                '"method": "SportsAPING/v1.0/listMarketBook",'\
                '"params": {"marketIds" : ["'+str(market_id)+'"],'\
                '"priceProjection":{"priceData":["EX_BEST_OFFERS"]}},'\
                '"id": 1}'
        market_response = self.call_api_ng(market_req)
        market_loads = json.loads(market_response)
        try:
            market_results = market_loads['result']
            return market_results
        except:
            raise CommandError(
                    'Exception from API-NG'\
                    + str(market_loads['error']))

    def handle(self, *args, **options):
        """Create odds for matches that haven't been played yet."""
        # Get all matches that haven't been played yet.
        matches = Match.objects.filter(completed=False)
        # Get a list of all event types in betfair.
        event_types = self.get_event_types()
        # Search for the 'soccer' event type id.
        soccer_event_type_id = self.get_event_type_id(
                event_types,
                'Soccer')
        # Get all soccer competitions.
        soccer_competitions = self.get_competitions(soccer_event_type_id)

        # Find the competition ids for specific competitions.
        competition_ids = {}
        competition_ids['English Premier League'] = self.get_competition_id(
                soccer_competitions, 'English Premier League')
        competition_ids['The Championship'] = self.get_competition_id(
                soccer_competitions, 'The Championship')

        for match in matches:
            competition_name = match.division.betfair_name
            competition_id = competition_ids[competition_name]

            # Get the betfair event id for the match using the
            # home/away team names in the text search string.
            event_id = self.get_event_id(
                    competition_id,
                    match.home_team.betfair_name,
                    match.away_team.betfair_name)

            market_id, markets = self.get_market_id(event_id)

            # TODO: should these names be extracted from betfair?
            over_under_market_name = 'Over/Under 2.5 Goals'
            match_odds_market_name = 'Match Odds'
            under_25_goals = 'Under 2.5 Goals'
            over_25_goals = 'Over 2.5 Goals'

            if markets[0]['marketName'] == over_under_market_name:
                over_under_market = markets[0]
                match_odds_market = markets[1]
            else:
                over_under_market = markets[1]
                match_odds_market = markets[0]

            # Extract the match odds from the betfair market.
            prices = {}
            for runner in match_odds_market['runners']:
                prices[runner['selectionId']] = {}
                prices[runner['selectionId']] = {
                    'name' : runner['runnerName']}

            match_odds_market_book = self.get_market_book(
                    match_odds_market['marketId'])

            try:
                for runner in match_odds_market_book[0]['runners']:
                    prices[runner['selectionId']].update({
                        'odds' : runner['ex']['availableToBack'][0]['price']
                    })
            except:
                self.stdout.write(self.style.ERROR(
                    'Failed to create odds for match "%s"' % (match))
                )
                continue

            # Extract the over/under odds from the betfair market
            over_under_prices = {}
            for runner in over_under_market['runners']:
                over_under_prices[runner['selectionId']] = {
                        'name' : runner['runnerName']}

            under_25_odds = 0
            over_25_odds = 0
            over_under_market_book = self.get_market_book(
                    over_under_market['marketId'])

            try:
                for runner in over_under_market_book[0]['runners']:
                    over_under_prices[runner['selectionId']].update({
                        'odds' : runner['ex']['availableToBack'][0]['price']
                    })
            except:
                self.stdout.write(self.style.ERROR(
                    'Failed to create odds for match "%s"' % (match))
                )
                continue

            odds, created = Odds.objects.get_or_create(match=match)

            for k, v in prices.items():
                if v['name'] == match.home_team.betfair_name:
                    odds.home = v['odds']
                elif v['name'] == match.away_team.betfair_name:
                    odds.away = v['odds']
                else:
                    odds.draw = v['odds']

            for selection_id, price_info in over_under_prices.items():
                if price_info['name'] == over_25_goals:
                    odds.over = price_info['odds']
                elif price_info['name'] == under_25_goals:
                    odds.under = price_info['odds']
            odds.save()

            action = "updated"
            if created: action = "created"
            self.stdout.write(self.style.SUCCESS(
                'Successfully %s odds for match "%s"' % (action, match))
            )
