import requests
import json
import re
import uuid


class FFDecksSquareParser:

    def __init__(self):
        self.square_url = 'https://fftcg.square-enix-games.com/en/get-cards'
        self.square_data = requests.get(self.square_url).text
        self.card_list = json.loads(self.square_data)['cards']

        self._square_to_ffdecks_keys = [
            ('Name_EN', 'name'),
            ('Power', 'power'),
            ('Rarity', 'rarity'),
            ('Multicard', 'is_multi_playable'),
            ('Job_EN', 'job'),
            ('Cost', 'cost'),
            ('Code', 'serial_number'),
            ('Type_EN', 'type'),
            ('Text_EN', 'abilities'),
            ('Ex_Burst', 'is_ex_burst'),
            ('Element', 'element'),
            ('Category_1', 'category'),
            ('images', 'image')
        ]

        self._extra_ffdecks_keys = ['datastore_id']

        self.output_cards = []

    @staticmethod
    def format_markup(string):

        # Weird issue with opus 13 summons
        # 13-012R
        # [[ex]][[br]]   EX BURST[[/]] -> [[br]][[ex]]EX BURST[[/]]
        string = re.sub(r'\[\[ex]]\[\[br]]\s*EX BURST\[\[/]]', '[[br]][[ex]]EX BURST[[/]]', string)

        # Weird issue where sometimes we have [[b]] [[/]] tags with nothing in them
        # 16-124H
        # [[b]] [[/]] -> ''
        string = re.sub(r'\[\[[bi]]]\s*\[\[/]]', ' ', string)

        # Weird issue where sometimes we have ex brackets that don't make sense
        # 4-130H
        # [[ex]][[br]][[/]] -> [[br]]
        string = re.sub(r'\[\[ex]]\[\[br]]\[\[/]]', '[[br]]', string)

        # Weird break issue with Sky Samurai
        # 15-003C
        # [[i]][[br]] -> [[br]][[i]]
        string = re.sub(r'\[\[i]]\[\[br]]', '[[br]][[i]]', string)

        # Spaces after [[br]]
        # [[br]]\s\s  -> [[br]]
        string = re.sub(r'(\[\[br]])(\s*)', r'\1', string)

        # Some times we see [[i]]Job[[/]] [[i]]Member of the Turks[[/]]
        # This is technically not wrong, but lets clean it up
        # [[i]]Job[[/]] [[i]]Member of the Turks[[/]] -> [[i]]Job Member of the Turks[[/]]
        string = re.sub(r'(\s*)(\[\[i]])(Job)(\[\[/]])(\s*)(\[\[i]])(.*?)(\[\[/]])(\s*)', r'\2\3\5\7\8', string)

        # Remove extra spaces on the ends of stuff inside brackets
        # [[s]]Grand Delta [[/]] -> [[s]]Grand Delta[[/]]
        # This should be the last thing we do before proceeding with markdown replacements
        # [[br]] never need to get closed so we ignore those
        string = re.sub(r'(\[\[[^br]+]])(\s*)(.*?)(\s*)(\[\[/]])', r'\1\3\5', string)

        # Markdown Starts Here

        # Italics
        # [[i]]stuff[[/]] -> ~stuff~
        # if re.search("Cherry Blossom", string):
        #     print('done')
        allowed_to_be_italics_regex = ['Job', "Card Name", 'Damage', 'Warp', 'Category', 'Card name', 'Ability Name']
        for expression in allowed_to_be_italics_regex:
            r = re.compile(fr'(\s*)(\[\[i]])({expression})(.*?)(\[\[/]])(\s*)')
            if expression in ['Damage', 'Warp']:
                string = re.sub(r, r'~\3\4~ ', string)
            else:
                string = re.sub(r, r' ~\3\4~ ', string)

        # Special Orange
        # [[s]]Angelo Cannon[[/]]
        string = re.sub(r'(\[\[s]])(\s*)(.*?)(\s*\[\[/]])(\s*)', r'%\3% ', string)

        # EX Burst logo
        # [[ex]]EX BURST[[/]]
        string = re.sub(r'(\[\[ex]])(.*?)(\[\[/]])(\s*)', '{x} ', string)
        string = string.replace('EX BURST', '{x}')

        # Damage/Warp dash
        # -- -> ―
        string = re.sub(r'(Damage|Warp)(.*?)(\s*--)(\s*)', r'\1\2―', string)

        # Brackets
        string = string.replace(u"\u300a", '{')
        string = string.replace(u"\u300b", '}')

        # Bold
        string = string.replace("Activate", "*Activate*")
        string = string.replace("Brave", "*Brave*")
        string = string.replace("Haste", "*Haste*")
        string = string.replace("Dull", "*Dull*")
        string = string.replace("Freeze", "*Freeze*")
        string = string.replace("First Strike", "*First Strike*")
        string = string.replace("Back Attack", "*Back Attack*")

        # Replace Fullwidth Numbers with normal numbers
        string = string.replace(u"\uFF11", '{1}')
        string = string.replace(u"\uFF12", '{2}')
        string = string.replace(u"\uFF13", '{3}')
        string = string.replace(u"\uFF14", '{4}')
        string = string.replace(u"\uFF15", '{5}')
        string = string.replace(u"\uFF16", '{6}')
        string = string.replace(u"\uFF17", '{7}')
        string = string.replace(u"\uFF18", '{8}')
        string = string.replace(u"\uFF19", '{9}')
        string = string.replace(u"\uFF10", '{0}')
        string = string.replace(u"\u2015", "-")  # Damage 5 from Opus X cards
        string = string.replace(u"\u00fa", "u")  # Cuchulainn u with tilda

        # Kanji elements to ffdecks
        string = string.replace(u"\u571F", '{e}')
        string = string.replace(u"\u6c34", '{w}')
        string = string.replace(u"\u706b", '{f}')
        string = string.replace(u"\u98a8", '{w}')
        string = string.replace(u"\u6c37", '{i}')
        string = string.replace(u"\u96f7", '{l}')

        # ffdecks
        string = string.replace(u"\u30C0"u"\u30EB", '{d}')
        string = string.replace('{S}', '{s}')
        string = string.replace('{C}', '{c}')

        # Remove {{ }}
        string = string.replace("{{", "{")
        string = string.replace("}}", "}")

        # Amidot
        string = string.replace('&middot;', u"\u00B7")
        string = re.sub(r'\s*u"\u00B7"\s*', '', string)

        # Weird issue where some cards have a [[br]] in the middle of italic tags
        # 4-055H
        # ~Card Name [[br]] Raya-O-Senna~ -> ~Card Name Raya-O-Senna~
        r = re.compile(r'~.*?~')
        matches = re.findall(r, string)

        for match in matches:
            if '[[br]]' in match:
                replacement_string = re.sub(r'\[\[br]]', '', match)
                string = string.replace(match, replacement_string)

        # Rest of [[i]] and [[/]] are errant, so we remove them
        string = re.sub(r'(\[\[i]]|\[\[/]])', '', string)

        # Minor fixes
        # ~Whatever~ , -> ~Whatever~,
        string = string.replace("~ ,", "~,")
        string = string.replace("~ .", "~.")
        string = string.replace("~ :", "~:")

        return string

    @staticmethod
    def element_to_word(string):
        # Replace Element Logos
        string = string.replace(u"\u571F", 'Earth')
        string = string.replace(u"\u6c34", 'Water')
        string = string.replace(u"\u706b", 'Fire')
        string = string.replace(u"\u98a8", 'Wind')
        string = string.replace(u"\u6c37", 'Ice')
        string = string.replace(u"\u5149", 'Light')
        string = string.replace(u"\u95c7", 'Dark')
        string = string.replace(u"\u96f7", 'Lightning')

        return string

    def MakeOutputCardList(self):

        # for card in [x for x in self.card_list if x['Code'] == "8-066C/3-071H"]:
        for card in self.card_list:
            card_cursor = {'octgn_id': str(uuid.uuid4())}  # Build our card as we go
            for key in card.keys():  # Iterate through cards keys to compare to what we want

                for key_map in self._square_to_ffdecks_keys:  # Iterate through our key_map

                    # key_map[0] = Square
                    # key_map[1] = FFDecks

                    if key == key_map[0]:  # If the cards key is equal to square key, we do work
                        if key == "Multicard" or key == "Ex_Burst":
                            if card[key] in [u'\u25CB', u'\u3007']:
                                card_cursor[key_map[1]] = True
                            else:
                                card_cursor[key_map[1]] = False

                        elif key == "Power":
                            try:
                                card_cursor[key_map[1]] = int(card[key])
                            except ValueError:
                                card_cursor[key_map[1]] = None

                        elif key == "Rarity":
                            rarities = {
                                "C": "Common",
                                "H": "Hero",
                                "L": "Legend",
                                "PR": "Promo",
                                "R": "Rare",
                                "S": "Starter",
                                "B": "Boss",
                            }
                            card_cursor[key_map[1]] = rarities.get(card[key])

                        elif key == "Text_EN":
                            abilities = self.format_markup(card[key]).split('[[br]]')
                            card_cursor[key_map[1]] = abilities

                        elif key == "Code":
                            if re.search(r'^\d+-\d{3}[a-zA-Z]$', card[key]):
                                card_cursor[key_map[1]] = card[key][:-1]
                            elif re.search(r'/', card[key]):
                                r = re.compile(
                                    r"^(.*?)([A-Z])(/)(.*)")  # Reprint logic only grab first (6-006C)/1-011C
                                card_cursor[key_map[1]] = re.search(r, card[key]).group(
                                    1)  # and strip letter output (6-006)
                            else:
                                card_cursor[key_map[1]] = card[key]

                        elif key == "Cost":
                            try:
                                card_cursor[key_map[1]] = int(card[key])
                            except:
                                card_cursor[key_map[1]] = 0

                        elif key == "Element":
                            if len(card[key].split('/')) == 1:
                                card_cursor['element'] = self.element_to_word(card[key])
                                card_cursor['elements'] = [self.element_to_word(card[key])]
                            else:
                                card_cursor['element'] = None
                                card_cursor['elements'] = [self.element_to_word(element) for element in
                                                           card[key].split('/')]

                        elif key == "images":
                            # This doesn't seem to be consistent in ffdecks
                            # Seems like last few sets are stored in "https://storage.googleapis.com/ffdecks-card-images/
                            root_url = "https://storage.googleapis.com/ffdecks-card-images/"
                            file_name = f'{card["Code"]}_eg.jpg'
                            card_cursor[key_map[1]] = root_url + file_name

                        elif key == "Category_1":
                            # Issue with break in Category_1
                            # 14-001C
                            # We just strip [[br]] if found in Category_1
                            category = card[key].replace('[[br]]', '')
                            category = self.format_markup(category)

                            # Issue where somtimes we have <space><amidot><space>$
                            # We remove the trailing amidot if we encounter this
                            # 15-132S
                            category = re.sub(r'\s*\u00B7\s*$', '', category)

                            card_cursor[key_map[1]] = category

                        else:
                            card_cursor[key_map[1]] = self.format_markup(card[key])

            self.output_cards.append(card_cursor)


card_client = FFDecksSquareParser()
card_client.MakeOutputCardList()

with open('cards.json', 'w') as outfile:
    json.dump(card_client.output_cards, outfile)
