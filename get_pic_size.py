from PIL import Image
import requests

url = 'https://a.thumbs.redditmedia.com/dt7igrh2wPL59urJlkoiNrSkyhKXEX4AfI13LfPxva8.jpg'

url = 'https://a.espncdn.com/photo/2019/0915/r598368_1296x729_16-9.jpg'

im = Image.open(requests.get(url, stream=True).raw)

width, height = im.size

print(f'width: {width}, height: {height}')

