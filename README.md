
br-scraper
==========

This is a simple Python module designed to scrape tables from the great baseball website baseball-reference.com. Instantiate the BRScraper class with an optional server argument that defaults to http://www.baseball-reference.com/. Call the method parse_tables() with a web page (everything in the URL after the server and slash) to scrape the data from it. So for example: 

```
import brscraper
scraper = brscraper.BRScraper()
data = scraper.parse_tables("teams/BOS/2011.shtml")
```

`data` will contain a dictionary of parseable tables by HTML id scraped from the indicated page, the 2011 Boston Red Sox season page. In this example (at the time of this writing), there were five such tables on the page in the example. To access the team pitching data, which is given the `team_pitching` id, just call `data["team_pitching"]`. 

Each such table is a list of dictionaries, where each item in the list represents a row of the table and the keys are the headers of the table. So in the above example, to get the ERA of the first pitcher listed in the table, you would write

```
>>> float(data["team_pitching"][0]["ERA"])
2.89
```

If a header does not have a name, it is assigned an empty string as its key. Continuing the same example, baseball-reference at current writing does not give a name to the column containing player names, and so to get that pitcher's name you would do the following: 

```
>>> data["team_pitching"][0][""]
u'Josh Beckett'
```

Note that you need to do your own conversions; everything is stored as a string; there is no attempt to guess at whether a data type should be a number or a string. In several cases numbers, strings, and/or blanks are all found in the same columns, so you'll probably need exception handling on the conversions as well. 

Some more examples can be seen in the unit test file brscraper_unittest.py, which is by no means comprehensive but shows a few of the different baseball-reference pages you can scrape data from. 

This was an ad-hoc script that I figured might as well go on Github; I don't plan to update it regularly. Thanks as well to baseball-reference.com for creating a wonderful resource for baseball statheads. 