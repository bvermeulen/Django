''' helper function to use pagination in marketstack to extract
    values above limit
'''
from concurrent.futures import ThreadPoolExecutor
import requests

def pagination_marketstack_threaded(
        url: str, token: str, symbol: str, set_total=None) -> list:
    ''' pagination using threading, all (up to 50 batches) are dealt
        with simultaneously
    '''
    def get_url(offset):
        params = {
            'symbols': symbol,
            'offset': offset,
            'access_key': token,
        }
        try:
            res = requests.get(url, params=params)

        except requests.exceptions.ConnectionError:
            res = -1

        return offset, res

    params = {
        'symbols': symbol,
        'offset': 0,
        'access_key': token,
    }

    # call the url a first time to determine the limit and total in order to
    # minimise the number of threads needed
    try:
        res = requests.get(url, params=params)
        limit = res.json().get('pagination').get('limit')

        if res:
            if set_total:
                total = set_total

            else:
                total = res.json().get('pagination').get('total')

            series = res.json().get('data', [])

    except (requests.exceptions.ConnectionError, AttributeError):
        return []

    if not series:
        return []

    # ThreadPoolExecutor maintains the order of res_list the same as the mapping
    # input order
    with ThreadPoolExecutor(max_workers=50) as pool:
        res_list = pool.map(get_url, [offset for offset in range(limit, total, limit)])

    for _, res in res_list:

        # if result of res is not valid, the integrity of the data cannot be guaranteed,
        # hence return an empty list
        if res == -1:
            return []

        series += res.json().get('data', [])

    return series


def pagination_marketstack(url, token, symbol, set_total=None):
    ''' basic pagination without threading, each batch is handled sequentially
    '''
    offset = 0
    params = {
        'symbols': symbol,
        'offset': offset,
        'access_key': token
    }

    try:
        res = requests.get(url, params=params)
        limit = res.json().get('pagination').get('limit')

        if res:
            if set_total:
                total = set_total

            else:
                total = res.json().get('pagination').get('total')

            pages = total // limit
            batch_series = res.json().get('data', [])

    except (requests.exceptions.ConnectionError, AttributeError):
        return []

    series = []

    for page in range(0, pages + 1):
        print(f'\rProcessing page {page:4} from '
              f'{offset:4} to {offset+limit:4} ...', end='')
        series += batch_series
        offset += limit
        params = {
            'symbols': symbol,
            'offset': offset,
            'access_key': token}
        try:
            res = requests.get(url, params=params)
            if res:
                batch_series = res.json().get('data', [])

            else:
                break

        except requests.exceptions.ConnectionError:
            break

    print()
    return series
