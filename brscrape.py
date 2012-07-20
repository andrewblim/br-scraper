
from bs4 import BeautifulSoup
import codecs
import cStringIO
import csv
import re
import urllib2

class BRScraper:
    
    def __init__(self, server_url="http://www.baseball-reference.com/"):
        self.server_url = server_url
    
    def parse_table(self, resource, table_ids=None):
        """
        Given a resource on the baseball-reference server (should consist of 
        the url after the hostname and slash), returns a dictionary keyed on 
        table id containing arrays of data dictionaries keyed on the header 
        columns. table_ids is a string or array of strings that can optionally 
        be used to filter out which stats tables to return. 
        """

        def is_parseable_table(tag):
            if not tag.has_key("class"): return False
            return tag.name == "table" and "stats_table" in tag["class"] and "sortable" in tag["class"]

        def is_parseable_row(tag):
            if not tag.name == "tr": return False
            if not tag.has_key("class"): return True  # permissive
            return "league_average_table" not in tag["class"] and "stat_total" not in tag["class"]

        if isinstance(table_ids, str): table_ids = [table_ids]

        soup = BeautifulSoup(urllib2.urlopen(self.server_url + resource))
        tables = soup.find_all(is_parseable_table)
        data = {}

        for table in tables:
            if table_ids == None or table["id"] in table_ids:
                data[table["id"]] = []
                headers = table.find("thead").find_all("th")
                header_names = []
                for header in headers:
                    if header.string == None: base_header_name = u""
                    else: base_header_name = header.string
                    if base_header_name in header_names:
                        i = 1
                        header_name = base_header_name + "_" + str(i)
                        while header_name in header_names:
                            i += 1
                            header_name = base_header_name + "_" + str(i)
                    else:
                        header_name = base_header_name
                    header_names.append(header_name)
                rows = table.find("tbody").find_all(is_parseable_row)
                for row in rows:
                    entries = row.find_all("td")
                    entry_data = []
                    for entry in entries:
                        if entry.string == None:
                            entry_data.append(u"")
                        else:
                            entry_data.append(entry.string)
                    if len(entry_data) > 0:
                        data[table["id"]].append(dict(zip(header_names, entry_data)))
        
        return data

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

if __name__ == "__main__":
    
    scraper = BRScraper()
    years = range(1962, 2012)
    
    teams_by_year = {}
    wins = {}
    losses = {}
    
    for year in years:
        resource = "leagues/MLB/" + str(year) + "-standings.shtml"
        print resource
        data = scraper.parse_table(resource)
        teams_by_year[year] = []
        for entry in data["expanded_standings_overall"]:
            teams_by_year[year].append(entry["Tm"])
            wins[entry["Tm"] + "-" + str(year)] = int(entry["W"])
            losses[entry["Tm"] + "-" + str(year)] = int(entry["L"])
    
    gameRange = range(1, 162)
    prediction_data = {}
    for game in gameRange: prediction_data[game] = []
    
    for year in sorted(teams_by_year):
        for team in sorted(teams_by_year[year]):
            yearTeamKey = team + "-" + str(year)
            if wins[yearTeamKey] + losses[yearTeamKey] != 162: continue   # to keep apples to apples
            resource = "teams/" + team + "/" + str(year) + "-schedule-scores.shtml"
            print resource
            data = scraper.parse_table(resource, table_ids="team_schedule")
            cur_rs = 0
            cur_ra = 0
            for entry in sorted(data['team_schedule'], key=lambda x: x["Rk"]):
                (cur_wins, cur_losses) = map(int, entry["W-L"].split("-"))
                cur_rs += int(entry["R"])
                cur_ra += int(entry["RA"])
                if cur_wins + cur_losses == 0: continue  # for the very rare tie, Cubs 1965
                cur_wpct = cur_wins / float(cur_wins + cur_losses)
                cur_pwpct = cur_rs ** 2 / float(cur_rs ** 2 + cur_ra ** 2)
                fwd_wins = wins[yearTeamKey] - cur_wins
                fwd_losses = losses[yearTeamKey] - cur_losses
                if fwd_wins + fwd_losses == 0: continue
                fwd_wpct = fwd_wins / float(fwd_wins + fwd_losses)
                prediction_data[cur_wins + cur_losses].append([yearTeamKey, fwd_wpct, cur_wpct, cur_pwpct])
    
    csv = UnicodeWriter(open('data.csv', 'w'))
    csv.writerow(['game', 'yearTeam', 'fwd_wpct', 'cur_wpct', 'cur_pwpct'])
    for game in prediction_data:
        for entry in prediction_data[game]:
            row = [game]
            row.extend(entry)
            csv.writerow(map(str, row))
    