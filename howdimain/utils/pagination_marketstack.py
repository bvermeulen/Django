''' helper function to use pagination in marketstack to extract
    values above limit
'''
import requests


def pagination_marketstack(url, token, symbol, set_total=None):
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

    except requests.exceptions.ConnectionError:
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
                batch_series = res.json().get('data', {})

            else:
                break

        except requests.exceptions.ConnectionError:
            break

    return series
