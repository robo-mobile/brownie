from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import telebot
import logging
import pygame
import pygame.camera
# import RPi.GPIO as GPIO
import threading
import time
import os
import smbus
import cv2


TOKEN = '258340710:AAHahf5i14VPyMDJm9xop89g86cLQC3V_MA'
ADMIN_USER_ID = 180168855
LED_PIN = 3
PIR_PIN = 11
VIDEO_FILE_FORMAT = '.mkv'

# Enable Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

isSensorEnabled = False
isMuteNotifications = False

last_chat_id = -1
keyboard = []

pygame.init()
pygame.camera.init()
pygame.camera.list_cameras()

# cam = pygame.camera.Camera("/dev/video0", (640, 426))
cam = pygame.camera.Camera("/dev/video2", (1280, 720))
bot = telebot.TeleBot(TOKEN)


def get_image_cv2():
    camera_port = 0
    camera = cv2.VideoCapture(camera_port)
    time.sleep(0.1)  # If you don't wait, the image will be dark
    return_value, image = camera.read()
    filename = datetime.now().strftime('%d-%m-%Y %H:%M:%S') + '.jpg'
    cv2.imwrite(filename, image)
    del(camera)  # so that others can use the camera as soon as possible


def hidro_and_temp():
    # https://github.com/Thinary/AHT10/blob/master/src/Thinary_AHT10.cpp
    # https://myhydropi.com/raspberry-pi-i2c-temperature-sensor
    # cleaned up and documented smbus 1 and some errors
    # GJ 03-2020
    # i2cdetect -y 0
    # Get I2C bus
    #bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
    bus = smbus.SMBus(1) # Rev 2 Pi uses 1
    # when you have a 121 IO Error, uncomment the next pause
    # time.sleep(1) #wait here to avoid 121 IO Error

    config = [0x08, 0x00]
    bus.write_i2c_block_data(0x38, 0xE1, config)
    time.sleep(0.5)
    byt = bus.read_byte(0x38)
    #print(byt&0x68)
    MeasureCmd = [0x33, 0x00]
    bus.write_i2c_block_data(0x38, 0xAC, MeasureCmd)
    time.sleep(0.5)
    data = bus.read_i2c_block_data(0x38,0x00)
    #print(data)
    temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    ctemp = ((temp*200) / 1048576) - 50
    print(u'Temperature: {0:.1f}°C'.format(ctemp))
    tmp = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    #print(tmp)
    ctmp = int(tmp * 100 / 1048576)
    print(f'Humidity: {ctmp}%')


# def setup():
#     GPIO.setmode(GPIO.BOARD)
#     GPIO.setwarnings(False)
#     GPIO.setup(LED_PIN, GPIO.OUT)
#     GPIO.setup(PIR_PIN, GPIO.IN)
#
#
# def destroy():
#     GPIO.output(LED_PIN, GPIO.LOW)
#     GPIO.cleanup()


def log_params(method_name, message):
    logger.debug(f'Method: {method_name}'
                 f'From: {message.from_user}'
                 f'chat_id: {message.chat.id}'
                 f'Text: {message.text}')


@bot.message_handler(commands=['start'])
def start(message):
    global keyboard

    log_params('start', message)

    telegram_user = message.from_user

    if telegram_user.id != ADMIN_USER_ID:
        bot.send_message(message.chat.id, text='Hello. My name is James '
                                               'Brown. What do i do for you?')

        return

    keyboard = [
        [InlineKeyboardButton("Start sensor", callback_data='start_sensor')],
        [
            InlineKeyboardButton("Get capture", callback_data='get_capture'),
            InlineKeyboardButton("Get video", callback_data='get_video')
        ],
    ]

    bot.send_message(chat_id=message.chat.id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def sendCapture(chat_id):
    filename = datetime.now().strftime('%d-%m-%Y %H:%M:%S') + '.jpg'

    if os.path.exists(filename):
        bot.send_photo(chat_id, photo=open(filename, 'rb'))
    else:
        cam.start()
        time.sleep(5)
        pygame.image.save(cam.get_image(), filename)
        cam.stop()

        bot.send_photo(chat_id, photo=open(filename, 'rb'))


def get_capture(chat_id):
    sendCapture(chat_id)
    bot.send_message(chat_id=chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def sendVideo(chat_id):
    filename = sorted(list(filter(lambda x: x.endswith(VIDEO_FILE_FORMAT), os.listdir())))[-1]

    bot.send_video(chat_id, open(filename, 'rb'))


def captureVideo():
    filename = datetime.now().strftime('%d-%m-%Y %H:%M:%S') + VIDEO_FILE_FORMAT

    os.system("ffmpeg -f v4l2 -framerate 25 -video_size 640x426 -i /dev/video2 -t 5 -c copy \"" + filename + "\"")

    return filename


def get_video(chat_id):
    bot.send_message(chat_id=chat_id,
                     text="Capturing video..")

    filename = captureVideo()

    bot.send_message(chat_id=chat_id,
                     text="Sending video..")
    bot.send_video(chat_id, open(filename, 'rb'))
    bot.send_message(chat_id=chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def sensorJob():
    global isSensorEnabled
    global keyboard

    isRecording = False

    # while isSensorEnabled:
    #     i = GPIO.input(PIR_PIN)
    #
    #     GPIO.output(LED_PIN, i)
    #
    #     if (i == 1 and not isRecording):
    #         isRecording = True
    #
    #         if (not isMuteNotifications):
    #             sendCapture(last_chat_id)
    #
    #     if (isRecording):
    #         captureVideo()
    #
    #     if (i == 0 and isRecording):
    #         if (not isMuteNotifications):
    #             sendVideo(last_chat_id)
    #
    #         isRecording = False
    #
    #     time.sleep(0.1)
    #
    # if (isRecording):
    #     sendVideo(last_chat_id)
    #
    # keyboard = [
    #     [InlineKeyboardButton("Start sensor", callback_data='start_sensor')],
    #     [
    #         InlineKeyboardButton("Get capture", callback_data='get_capture'),
    #         InlineKeyboardButton("Get video", callback_data='get_video')
    #     ],
    # ]

    bot.send_message(chat_id=last_chat_id,
                     text="Sensor stopped")
    bot.send_message(chat_id=last_chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def start_sensor(chat_id):
    global keyboard
    global isSensorEnabled
    global last_chat_id

    last_chat_id = chat_id
    isSensorEnabled = True

    threading.Thread(target=sensorJob).start()

    keyboard = [
        [
            InlineKeyboardButton("Stop sensor", callback_data='stop_sensor'),
            InlineKeyboardButton("Mute notifications", callback_data='mute_notifications')
        ]
    ]

    bot.send_message(chat_id=chat_id,
                     text="Sensor started")
    bot.send_message(chat_id=chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def stop_sensor(chat_id):
    global keyboard
    global last_chat_id

    last_chat_id = -1
    isSensorEnabled = False

    # GPIO.output(LED_PIN, GPIO.LOW)

    keyboard = [
        [InlineKeyboardButton("Start sensor", callback_data='start_sensor')],
        [
            InlineKeyboardButton("Get capture", callback_data='get_capture'),
            InlineKeyboardButton("Get video", callback_data='get_video')
        ],
    ]

    bot.send_message(chat_id=chat_id,
                     text="Sensor stop requested")


def mute_notifications(chat_id):
    global keyboard

    isMuteNotifications = True

    keyboard = [
        [
            InlineKeyboardButton("Stop sensor", callback_data='stop_sensor'),
            InlineKeyboardButton("Unmute notifications", callback_data='unmute_notifications')
        ]
    ]

    bot.send_message(chat_id=chat_id,
                     text="Notifications muted")
    bot.send_message(chat_id=chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


def unmute_notifications(chat_id):
    global keyboard

    isMuteNotifications = False

    keyboard = [
        [
            InlineKeyboardButton("Stop sensor", callback_data='stop_sensor'),
            InlineKeyboardButton("Mute notifications", callback_data='mute_notifications')
        ]
    ]

    bot.send_message(chat_id=chat_id,
                     text="Notifications unmuted")
    bot.send_message(chat_id=chat_id,
                     text="Supported commands:",
                     reply_markup=InlineKeyboardMarkup(keyboard))


@bot.callback_query_handler(func=lambda call: True)
def button(call):
    globals()[call.data](call.message.chat.id)


def main():
    # setup()
    bot.polling(none_stop=False, interval=5, timeout=20)
    # destroy()


if __name__ == '__main__':
    main()
