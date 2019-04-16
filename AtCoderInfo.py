import requests
import bs4

url = 'https://atcoder.jp/ranking?f.UserScreenName='

def get_user(userName):
    q = requests.get(url+userName)
    html = bs4.BeautifulSoup(q.text, 'html.parser')
    elem = html.select('.username')
    if len(elem) == 0:
        return {
                'name': userName,
                'global_rank': 0,
                'local_rank': 0,
                'affiliation': '',
                'rating': 0,
                'highest_rating': 0,
                'competitions': 0,
                'wins': 0,
                }
    name = html.select('.username')[0].text
    rank = html.select('td.no-break')[0].text.split()
    global_rank = int(rank[0])
    local_rank = int(rank[1][1:-1]) if len(rank) >= 2 else 0
    affiliation = html.select('.ranking-affiliation')[0].text
    rating = html.select('td.no-break ~ td')[2].text
    rating_max = html.select('td.no-break ~ td')[3].text
    competition_count = html.select('td.no-break ~ td')[4].text
    wins = html.select('td.no-break ~ td')[5].text
    return {
            'name': name,
            'global_rank': global_rank,
            'local_rank': local_rank,
            'affiliation': affiliation,
            'rating': int(rating),
            'highest_rating': int(rating_max),
            'competitions': int(competition_count),
            'wins': int(wins)
            }

