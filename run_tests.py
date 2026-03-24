import os
import time


TEST_GOODS = [
    {
        'query': 'футболка',
        'sku': '491535181'
    },
    {
        'query': 'умные часы',
        'sku': '1273722552'
    },
    {
        'query': 'наушники',
        'sku': '1642477586'
    }
]


if __name__ == '__main__':
    for i, test_good in enumerate(TEST_GOODS):
        os.system(f'python script.py "{test_good["query"]}" "{test_good["sku"]}"')
        if i != len(TEST_GOODS) - 1:
            time.sleep(30)
