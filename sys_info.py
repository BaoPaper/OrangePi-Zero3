import requests
import psutil
import time
import datetime
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from PIL import Image, ImageDraw
import subprocess

i2c_bus_number = 3 #定义i2c总线
first_run = True  # 标记是否第一次运行脚本
serial = i2c(port=i2c_bus_number, address=0x3C)  # 设置 OLED I2C 地址
device = ssd1306(serial)
location = ""  # 地理位置代码
key = ""  # 和风天气API密钥

# 获取系统信息
def get_system_info():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    CPU = f"CPU: {cpu_percent:.2f}%"

    mem = psutil.virtual_memory()
    mem_usage = f"Mem: {mem.used/1024/1024/1024:.1f}/{mem.total/1024/1024/1024:.1f} GB {mem.percent:.1f}%"
    
    disk = psutil.disk_usage('/')
    disk_usage = f"Disk: {disk.used/1024/1024/1024:.1f}/{disk.total/1024/1024/1024:.1f} GB {disk.percent}%"

    IP = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip().split()[0]
    cmd = "cat /sys/class/thermal/thermal_zone0/temp | awk '{printf \"%.1f\", $0/1000}'"
    cput = subprocess.check_output(cmd, shell=True).decode('utf-8')

    return CPU, mem_usage, disk_usage, IP, cput

# 获取天气信息
def get_weather():
    url = "https://devapi.qweather.com/v7/weather/now"

    params = {
        "location": location,
        "key": key
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['code'] == "200":
            weather = data["now"]["text"]
            temperature = data["now"]["temp"]

            return f'沙市区 {weather} {temperature}℃'
        else:
            return '请求失败'
    except Exception as e:
        return f'发生异常：{str(e)}'

# 格式化运行时间
def format_uptime(uptime):
    total_seconds = int(uptime.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# 显示开机欢迎信息
def show_poweron_text(draw, font_Big, width, height):
    font_path = "apple-M.ttf"  # 替换为实际的字体文件路径
    font_size = 15  # 指定字体大小
    font = ImageFont.truetype(font_path, font_size)

    # 加载图像
    image_path = "start.png"
    image_to_display = Image.open(image_path).convert("1")  # 转换为单色模式

    # 缩放图像以适应屏幕大小
    image_to_display = image_to_display.resize((width, height))

    # 创建一个可以在图像上绘制文本的 Draw 对象
    draw = ImageDraw.Draw(image_to_display)

    # 在屏幕上显示图像
    device.display(image_to_display)

def main():
    global first_run

    width = 128
    height = 64
    # 创建一个黑色背景的空白图像
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)

    # 定义字体大小
    font_size_Big = 18  # 大字体大小
    font_size_large = 14  # 中字体大小
    font_size_small = 10  # 小字体大小
    font_Big = ImageFont.truetype("apple-M.ttf", font_size_Big)
    font_large = ImageFont.truetype("apple-M.ttf", font_size_large)
    font_small = ImageFont.truetype("apple-M.ttf", font_size_small)

    last_switch_time = time.time()# 获取当前时间
    showing_system_info = True    # 是否显示系统信息
    poweron_displayed = False    # 是否已显示开机信息

    result = get_weather()

    # 获取系统启动时间
    boot_time = psutil.boot_time()
    boot_time_datetime = datetime.datetime.fromtimestamp(boot_time)

    # 主循环
    while True:
        if not poweron_displayed:       # 如果尚未显示开机信息
            show_poweron_text(draw, font_Big, width, height)
            poweron_displayed = True
            time.sleep(3)
            device.display(image)

        if poweron_displayed and time.time() - last_switch_time >= 3:  # 等待3秒后开始切换显示内容
            # 如果显示系统信息
            CPU, MemUsage, Disk, IP, cput = get_system_info()

            # 清除之前的内容
            draw.rectangle((0, 0, width - 1, height - 1), outline=0, fill=0)
            top = 0

            # 重新绘制数据
            draw.text((0, top), CPU, font=font_small, fill=255)
            draw.text((80, top), cput + " °C", font=font_small, fill=255)
            top += 12
            draw.text((0, top), MemUsage.replace('%', '% '), font=font_small, fill=255)
            top += 12
            draw.text((0, top), Disk, font=font_small,fill=255)
            top += 12
            draw.text((0, top), "IP: " + IP, font=font_small, fill=255)
            top += 12
            # 绘制分隔线
            draw.line((0, top, width, top), fill=255)
            draw.text((0, top), result, font=font_large, fill=255)
        
        # 如果距离天气刷新时间超过900秒，刷新天气信息
        if time.time() - last_switch_time >= 900:
            result = get_weather()

        # 在 OLED 屏幕上显示图像
        device.display(image)
        time.sleep(5)
        last_switch_time = time.time()  # 刷新天气更新时间

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("An error occurred:", str(e))
        serial.cleanup()  # 如果需要，确保在发生异常时进行清理操作