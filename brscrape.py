
from bs4 import BeautifulSoup
import codecs
import cStringIO
import csv
import re
import urllib2

br_server = "http://www.baseball-reference.com/"

# UnicodeWriter taken from the Python 2.7.3 Library Reference

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


def parse_table(resource, table_ids=None):
    """docstring"""
    
    def is_parseable_table(tag):
        if not tag.has_key("class"): return False
        return tag.name == "table" and "stats_table" in tag["class"] and "sortable" in tag["class"]
    
    if isinstance(table_ids, str): table_ids = [table_ids]
    
    soup = BeautifulSoup(urllib2.urlopen(br_server + resource))
    tables = soup.find_all(is_parseable_table)
    for table in tables:
        if table_ids == None or table["id"] in table_ids:
            csv_filename = re.sub("\W", "_", resource) + "-" + table["id"] + ".csv"
            writer = UnicodeWriter(open(csv_filename, 'w')) # csv.writer(open(csv_filename, 'w'))
            headers = table.find("thead").find_all("th")
            header_names = []
            for header in headers:
                if header.string == None:
                    header_names.append(u"")
                else:
                    header_names.append(header.string)
            print header_names
            writer.writerow(header_names)
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                entries = row.find_all("td")
                data = []
                for entry in entries:
                    if entry.string == None:
                        data.append(u"")
                    else:
                        data.append(entry.string)
                writer.writerow(data)

if __name__ == "__main__":
    # parse_table("players/g/greinza01.shtml")
    parse_table("teams/BOS/2011-schedule-scores.shtml")