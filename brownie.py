import csv
from datetime import datetime
import time
import logging
from aht10 import getTempHum

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


def create_data():
    row = []
    date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    dat = getTempHum()
    row.append(date)
    row.append(dat[0])
    row.append(dat[1])
    logging.debug(f'Data {row}')
    return row


def write_to_file(row: list):
    # open the file in the write mode
    with open('./data.csv', 'a', encoding='UTF8') as f:
        # create the csv writer
        writer = csv.writer(f)
        data2 = "some"
        # write a row to the csv file
        writer.writerow(row)


if __name__ == '__main__':
    while True:
        data = create_data()
        write_to_file(data)
        time.sleep(10)
