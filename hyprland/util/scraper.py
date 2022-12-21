import requests
import bs4

def get_dat():
    raw = requests.get('https://wiki.hyprland.org/Configuring/Variables/#sections').text
    dat = {}
    soup = bs4.BeautifulSoup(raw, 'html.parser')
    sections = soup.find('h1', id = 'sections')
    if sections and sections.parent:
        blocks = sections.parent.findAllNext(class_='gdoc-page__anchorwrap')
        for block in blocks:
            name = block.find('h2') or block.find('h1')
            if name:
                table = block.next_sibling.find('table')
                if table and table.name == 'table':
                    dat[name.text.strip()] = []
                    for row in table.findAll('tr'):
                        cells = [cell.text.strip() for cell in row.findAll('td')]
                        if len(cells) >= 4:
                            dat[name.text.strip()].append({
                                    'name': cells[0],
                                    'desc': cells[1],
                                    'type': cells[2],
                                    'default': cells[3],
                            })
    return dat

def parse_val(s,t):
    if s == '[EMPTY]':
        return None
    elif s in ['true','yes','on']:
        return True
    elif s in ['false','no','off']:
        return False
    elif s == 'unset':
        return None
    else:
        match t:
            case 'int':
                return int(s)
            case 'float':
                return float(s)
            case 'color':
                return int(s, 16)
            case _:
                print('Unknown type: ' + t)
                return f'\'{s}\''


if __name__ == '__main__':

    from rich.console import Console
    import json


    console = Console()

    console.log('starting scrape')
    dat = get_dat()
    console.log('output written to file: sections.json')

    with open('settings.py','w') as f:
        f.write('""" This file is generated by util/scraper.py """\n\n')
        f.write('class _Config():\n    def __init__(self,sock):\n        self.sock = sock\n\n    def __setattr__(self, attr, value):\n        print(f\'config {self.__class__.__name__}: {attr} = {value}\')\n        super().__setattr__(attr, value)\n\n')
        setting_class = f'\nclass Defaults:\n\n    def __init__(self,sock):\n        self.sock = sock\n\n'
        for section in dat:
            f.write(f'''class {section}(_Config):\n\n    def __init__(self,sock):\n        super().__init__(sock)\n\n\n''')
            for setting in dat[section]:
                f.write(f'    {setting["name"].replace(".","__")} = {parse_val(setting["default"],setting["type"])}\n')
                f.write(f'    """ {setting["desc"]} """\n\n')
            setting_class += f'        self.{section.lower()} = {section}(self.sock)\n'
        f.write(setting_class)