import requests
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from PIL import Image, ImageDraw

# 定义屏幕尺寸
width = 128
height = 64

# 创建 I2C 串行接口
serial = i2c(port=3, address=0x3C)

# 创建 SSD1306 OLED 设备
device = ssd1306(serial)

# 创建空白图像
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# 定义字体和字体大小
font_path = "apple-M.ttf"  # 替换为实际的字体文件路径
font_size = 20
font = ImageFont.truetype(font_path, font_size)

# 获取天气信息函数
def get_weather(city_name):
    url = f'https://api.axtn.net/api/weather?name={city_name}'

    response = requests.get(url)
    data = response.json()

    if data['code'] == 200:
        city = data['city']
        weather = data['weather']
        temperature = data['temperature']

        return f'{city} {weather} {temperature}℃'
    else:
        return '请求失败'

# 调用函数并输出结果到屏幕
city_name = '沙市区'
result = get_weather(city_name)

# 在图像上绘制天气信息文本
draw.text((10, 30), result, font=font, fill=255)

# 在屏幕上显示图像
device.display(image)