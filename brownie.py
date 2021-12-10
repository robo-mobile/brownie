import csv
from datetime import datetime
import time
import logging
from aht10 import getTempHum

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


def create_data():
    date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    dat = getTempHum
    data = f"{date};{dat(0)};{dat(1)}"
    logging.debug(f'Data {data}')
    return data


def write_to_file(data):
    # open the file in the write mode
    with open('./data.csv', 'w', encoding='UTF8') as f:
        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        writer.writerow(data)


if __name__ == '__main__':
    while True:
        data = create_data()
        write_to_file(data)
        time.sleep(10)
