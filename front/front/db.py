import aerospike
from front.models import UserProfile, UserTag
import snappy
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from typing import List

class UserProfileDAO:
    def __init__(self):
        self.NAMESPACE = 'mimuw'
        # self.NAMESPACE = 'test'
        self.SET = 'user_profile'
        self.RETRY_COUNT = 3

        config = {
            'hosts': [('st117vm106.rtb-lab.pl', 3000),
                      ('st117vm107.rtb-lab.pl', 3000),
                      ('st117vm108.rtb-lab.pl', 3000),
                      ('st117vm109.rtb-lab.pl', 3000),
                      ('st117vm110.rtb-lab.pl', 3000)],
            # 'hosts': [('aerospike', 3000)],
            'policies': {
                    'read': {
                        'replica': aerospike.POLICY_REPLICA_ANY,
                        'socket_timeout': 50,
                    },
                    'write': {
                        'commit_level': aerospike.POLICY_COMMIT_LEVEL_MASTER,
                        'exists': aerospike.POLICY_EXISTS_CREATE_OR_REPLACE,
                    }
            }
        }

        self.client = aerospike.client(config).connect()
    
    def get(self, cookie: str) -> UserProfile:
        profile, _, = self._get(cookie)
        return profile

    def _get(self, cookie: str) -> tuple[UserProfile, int]:
        key = (self.NAMESPACE, self.SET, cookie)

        try:
            (_, meta, compressed) = self.client.get(key)
            decompressed = snappy.decompress(compressed['data'])

            user_profile = UserProfile.model_validate_json(decompressed)
            generation = meta['gen']
        except:
            return None, None
        
        return user_profile, generation
    
    def _put(self, user_profile: UserProfile, generation: int) -> bool:
        key = (self.NAMESPACE, self.SET, user_profile.cookie)
        
        json = user_profile.model_dump_json()
        compressed = snappy.compress(json)

        try:
            self.client.put(key, {'data': compressed}, meta={'gen': generation}, policy={'gen': aerospike.POLICY_GEN_EQ})
        except aerospike.exception.RecordGenerationError:
            return False
        
        return True
        
    def _add_tag(self, user_tag: UserTag) -> bool:
        profile, generation = self._get(user_tag.cookie)
        if profile is None:
            profile = UserProfile(cookie = user_tag.cookie, views = [], buys = [])
            generation = 0

        if user_tag.action == "VIEW":
            profile.views.append(user_tag)
            profile.views.sort(key=lambda tag: datetime.fromisoformat(tag.time[:-1]))
            if len(profile.views) > 200:
                profile.views.pop(0)
        elif user_tag.action == "BUY":
            profile.buys.append(user_tag)
            profile.buys.sort(key=lambda tag: datetime.fromisoformat(tag.time[:-1]))
            if len(profile.buys) > 200:
                profile.buys.pop(0)
        
        return self._put(profile, generation)

    def add_tag(self, user_tag: UserTag):
        for _ in range(self.RETRY_COUNT):
            if self._add_tag(user_tag):
                return

        print('Failed to add tag')


    def __del__(self):
        self.client.close()

@dataclass
class AnalyticsQuery:
    action: str
    aggregates: List[str]
    origin: str | None
    brand_id: str | None
    category_id: str | None

class AnalyticsDAO:
    def __init__(self):
        self.NAMESPACE = 'mimuw'
        # self.NAMESPACE = 'test'
        self.SET = 'analytics'

        config = {
            'hosts': [('st117vm106.rtb-lab.pl', 3000),
                      ('st117vm107.rtb-lab.pl', 3000),
                      ('st117vm108.rtb-lab.pl', 3000),
                      ('st117vm109.rtb-lab.pl', 3000),
                      ('st117vm110.rtb-lab.pl', 3000)],
            # 'hosts': [('aerospike', 3000)],
            'policies': {
                    'read': {
                        'replica': aerospike.POLICY_REPLICA_ANY,
                        'socket_timeout': 50,
                    },
                    'write': {
                        'commit_level': aerospike.POLICY_COMMIT_LEVEL_MASTER,
                        'exists': aerospike.POLICY_EXISTS_CREATE_OR_REPLACE,
                    }
            }
        }

        self.client = aerospike.client(config).connect()

    def _build_keys(self, start: str, end: str, query: AnalyticsQuery):
        cur_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)

        times = []
        while cur_time < end_time:
            times.append(cur_time.strftime("%Y-%m-%dT%H:%M:00"))
            cur_time += timedelta(minutes=1)

        params = []
        params.append(query.action)
        if query.origin is not None:
            params.append(query.origin)
        if query.brand_id is not None:
            params.append(query.brand_id)
        if query.category_id is not None:
            params.append(query.category_id)

        keys = []
        for time in times:
            key = json.dumps([time] + params)
            keys.append((self.NAMESPACE, self.SET, key))

        return keys
    
    def _get_header(self, query: AnalyticsQuery):
        header = ["1m_bucket", "action"]
        if query.origin is not None:
            header.append("origin")
        if query.brand_id is not None:
            header.append("brand_id")
        if query.category_id is not None:
            header.append("category_id")

        for aggregate in query.aggregates:
            header.append(aggregate.lower())

        return header

    def get_batch(self, start: str, end: str, query: AnalyticsQuery):
        keys = self._build_keys(start, end, query)
        records = self.client.get_many(keys)

        header = self._get_header(query)
        rows = []
        for key, _, record in records:
            row = json.loads(key[2])

            for aggregate in query.aggregates:
                if record:
                    row.append(str(record.get(aggregate, 0)))
                else:
                    row.append(str(0))

            rows.append(row)

        return {'columns': header, 'rows': rows}

    def __del__(self):
        self.client.close()