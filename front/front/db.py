import aerospike
from front.models import UserProfile, UserTag
import snappy

class UserProfileDAO:
    def __init__(self):
        # self.NAMESPACE = 'test'
        self.NAMESPACE = 'mimuw'
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
                    },
                    'write': {
                        'commit_level': aerospike.POLICY_COMMIT_LEVEL_MASTER,
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
            print("generation error")
            return False
        
        return True
        
    def _add_tag(self, user_tag: UserTag) -> bool:
        profile, generation = self._get(user_tag.cookie)
        if profile is None:
            profile = UserProfile(cookie = user_tag.cookie, views = [], buys = [])
            generation = 0

        if user_tag.action == "VIEW":
            profile.views.append(user_tag)
            if len(profile.views) > 200:
                profile.views.pop(0)
        elif user_tag.action == "BUY":
            profile.buys.append(user_tag)
            if len(profile.buys) > 200:
                profile.buys.pop(0)
        
        return self._put(profile, generation)

    def add_tag(self, user_tag: UserTag):
        for _ in range(self.RETRY_COUNT):
            if self._add_tag(user_tag):
                return

        raise Exception('Failed to add tag')


    def __del__(self):
        self.client.close()