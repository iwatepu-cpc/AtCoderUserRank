import AtCoderInfo
import json
import sys

cache_path = ''
user_list_path = ''

class AtCoderInfoCache:
    def __init__(self, cache_path, user_list_path):
        self.cache_path = cache_path
        self.user_list_path = user_list_path
        self.cache = AtCoderInfoCache.__load_cache(cache_path)
        self.user_list = AtCoderInfoCache.__load_user_list(user_list_path)
        print(self.user_list)
        if self.user_list is None:
            raise Error('UserList file not found: {}'.format(user_list_path))
        if self.cache is None:
            self.cache = {username:AtCoderInfo.get_user(username) for username in self.user_list}
            AtCoderInfoCache.__save_cache(cache_path, self.cache)

    def get_latest(self):
        records = {username:AtCoderInfo.get_user(username) for username in self.user_list}
        AtCoderInfoCache.__save_cache(self.cache_path, records)
        diffs = {username:AtCoderInfoCache.__diff_record(records[username], self.cache[username]) for username in self.user_list if username in self.cache}
        return records, diffs

    def __load_cache(path):
        try:
            with open(path) as f:
                cache = json.load(f)
        except:
            cache = None
        return cache

    def __load_user_list(path):
        try:
            with open(path) as f:
                ul = f.read().strip().split('\n')
        except:
            ul = None
        return ul

    def __save_cache(path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def __diff_record(new, old):
        return {
                'name': new['name'],
                'global_rank': old['global_rank'] - new['global_rank'],
                'local_rank': old['local_rank'] - new['local_rank'],
                'rating': new['rating'] - old['rating'],
                'highest_rating': new['highest_rating'] - old['highest_rating'],
                'competitions': new['competitions'] - old['competitions'],
                'wins': new['wins'] - old['wins'],
                }

