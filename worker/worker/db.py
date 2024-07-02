import aerospike
from worker.models import UserTag
import snappy
import json

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
                        'total_timeout': 60000,
                    },
                    'write': {
                        'commit_level': aerospike.POLICY_COMMIT_LEVEL_MASTER,
                        'exists': aerospike.POLICY_EXISTS_CREATE_OR_REPLACE,
                    }
            }
        }

        self.client = aerospike.client(config).connect()
    
    def _increment(self, id: str, bin: str, amount: int):
        key = (self.NAMESPACE, self.SET, id)

        try:
            self.client.increment(key, bin, amount)
        except aerospike.exception.RecordNotFound:
            self.client.put(key, {bin: amount})
        except Exception as e:
            pass

    def increment_all(self, user_tag: UserTag):
        time_bucket = user_tag.time[:-7] + '00'

        # Always present: action, aggregate
        # Possibly empty: origin, brand_id, category_id
        for aggregate in ['COUNT', 'SUM_PRICE']:
            amount = 1 if aggregate == 'COUNT' else user_tag.product_info.price

            key = [time_bucket, user_tag.action]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.origin]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.product_info.brand_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.product_info.category_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.origin, user_tag.product_info.brand_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.origin, user_tag.product_info.category_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.product_info.brand_id, user_tag.product_info.category_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

            key = [time_bucket, user_tag.action, user_tag.origin, user_tag.product_info.brand_id, user_tag.product_info.category_id]
            key_compressed = json.dumps(key)
            self._increment(key_compressed, aggregate, amount)

    def __del__(self):
        self.client.close()