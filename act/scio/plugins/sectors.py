import addict
from act.scio.vocabulary import Vocabulary
from act.scio.plugin import BasePlugin, Result
from typing import Text, List
import configparser
import nltk
import nltk.stem
import os


class Plugin(BasePlugin):
    name = "sectors"
    info = "Extract sectors from a body of text"
    version = "0.1"
    dependencies: List[Text] = ["pos_tag"]

    async def analyze(self, nlpdata: addict.Dict) -> Result:

        res = addict.Dict()

        sector_stem_postfix = {
            'compani',  # company, companies, [...],
            'industri',  # industry, industries, [...],
            'sector',   # sector, sectors, [...],
            'servic',   # service, services, [...],
            'organ',   # organization, organizations, [...],
            'provid',  # provider, providers, [...],
        }

        posible_tag_types = {"NNP", "NNPS", "NN", "NNS"}
        lookbefore_tags = {",", ":", "CC"}
        lookbefore_tags.update(posible_tag_types)

        ps = nltk.stem.PorterStemmer()

        pos_sectors: List[Text] = []
        # Look through all tokens. If any token relating to a sector is found,
        # look-before and collect all nouns while the tokens are nouns or part
        # of a listing.
        for i, (token, tag) in enumerate(nlpdata.pos_tag.tokens):
            if tag in posible_tag_types and ps.stem(token) in sector_stem_postfix:
                n = i - 1
                while nlpdata.pos_tag.tokens[n][1] in lookbefore_tags:
                    n -= 1
                pos_sectors += [token for (token, pos_tag)
                                in nlpdata.pos_tag.tokens[n:i]
                                if pos_tag in posible_tag_types]

        ini = configparser.ConfigParser()
        ini.read([os.path.join(self.configdir, "sectors.ini")])
        ini['sectors']['alias'] = os.path.join(self.configdir, ini['sectors']['alias'])

        vocab = Vocabulary(ini['sectors'])
        sectors = []
        unknown_sectors = []
        for pos_sector in pos_sectors:
            primary = vocab.get(pos_sector, primary=True)
            if primary:
                sectors.append(primary)
            else:
                unknown_sectors.append(pos_sector)

        res.sectors = sectors
        res.unknown_sectors = unknown_sectors
        return Result(name=self.name, version=self.version, result=res)
