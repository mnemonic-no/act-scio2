import addict
from act.scio.plugin import BasePlugin, Result
from act.scio.vocabulary import Vocabulary
from typing import Text, List, Tuple, Dict, Set
import configparser
import csv
import json
import os


class Plugin(BasePlugin):
    name = "locations"
    info = "Extract locations from a body of text"
    version = "0.1"
    dependencies: List[Text] = ["pos_tag"]

    def nouns(self, tok: List[Tuple[Text, Text]]) -> List[Text]:
        """Rebuild a list of nouns from the tokenized values. e.g.
        [('The', 'DT'), ('Arabic', 'NNP'), ('Emirates', 'NNP')] will return
        ["Arabic Emirates"]"""

        res: Set[Text] = set()
        curr_name: List[Text] = []
        curr_in_name: List[Text] = []
        for i, (token, tag) in enumerate(tok):
            if tag == "NNP":
                # do not keep first part of Noun containing a preposition/subordinating conjunction.
                # e.g. do not keep "Republic" when what we are working on is "Republic of Congo"
                if i < len(tok) - 1 and tok[i+1][1] != "IN":
                    curr_name.append(token)
                curr_in_name.append(token)
            elif tag == "IN":
                if curr_in_name:
                    curr_in_name.append(token)
                if curr_name:
                    res.add(" ".join(curr_name))
                    curr_name = []
            else:
                if curr_name:
                    res.add(" ".join(curr_name))
                    curr_name = []
                if curr_in_name:
                    res.add(" ".join(curr_in_name))
                    curr_in_name = []

        if curr_name:
            res.add(" ".join(curr_name))
        if curr_in_name:
            res.add(" ".join(curr_in_name))

        return list(res)

    def cities_from_file(self, filename: Text) -> Dict[Text, Dict]:
        reader = csv.reader(open(filename), dialect="excel-tab")
        ret: Dict[Text, Dict] = {}
        for _, city, _, _, _, _, _, _, cc, _, _, _, _, _, pop, _, _, area, _ in reader:
            city = city.split(",")[0]
            if (city in ret and ret[city]['population'] < int(pop)) or city not in ret:
                ret[city] = addict.Dict({
                    'name': city,
                    'population': int(pop),
                    'country code': cc,
                    'area': area,
                })
        return ret

    def countries_from_file(self, filename: Text) -> Tuple[Dict, Dict]:

        names: Dict = {}
        alpha2: Dict = {}

        countries = json.load(open(filename))

        for country in countries:
            names[country['name']] = addict.Dict(country)
            alpha2[country['alpha-2']] = addict.Dict(country)

        return names, alpha2

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        res = addict.Dict()

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "locations.ini")])
        ini['locations']['cities'] = os.path.join(self.configdir,
                                                  "../../vendor",
                                                  ini['locations']['cities'])
        ini['locations']['countries'] = os.path.join(self.configdir,
                                                     "../../vendor",
                                                     ini['locations']['countries'])
        ini['vocabulary']['alias'] = os.path.join(self.configdir, ini['vocabulary']['alias'])

        cities = self.cities_from_file(ini['locations']['cities'])
        country_names, country_cc = self.countries_from_file(ini['locations']['countries'])

        nouns = self.nouns(nlpdata.pos_tag.tokens)
        vocab = Vocabulary(ini['vocabulary'])

        res.cities = []
        res.countries = []
        res.countries_inferred = []
        res.countries_mentioned = []

        for noun in nouns:
            if noun in cities:
                city = cities[noun]
                res.cities.append(city)
                res.countries_inferred.append(country_cc.get(city['country code'], "UNK"))
            if noun in country_names:
                res.countries.append(country_names[noun])
            if vocab.get(noun):
                res.countries_mentioned.append(noun)

        return Result(name=self.name, version=self.version, result=res)
