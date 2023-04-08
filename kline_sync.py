import os,time,os.path,datetime,traceback,json
import fire
import xml.etree.ElementTree as ET
import pandas as pd
import urllib

def sync_symbols():
    cmd = f""" curl -s https://api.binance.com/api/v3/exchangeInfo | jq '.symbols[] | select(.permissions[]? == "SPOT") | .symbol' > symbols.txt """
    print(cmd)
    os.system(cmd)
    for line in open("symbols.txt").readlines():
        name = line.strip().replace('"','')
        cmd = f'''wget -c -qO-  --header="Accept: application/xml" "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/daily/klines/{name}/1m/" 
        | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g; s/&apos;/\\x27/g; s/&quot;/"/g' | xmllint --format - | grep '<Key>' | sed 's/<Key>\(.*\)<\/Key>/\\1/g' | grep -v CHECKSUM > files.txt'''
        print(cmd)
        os.system(cmd)
        for fn in open("files.txt").readlines():
            fn = fn.strip()
            path,f = os.path.split(fn)
            os.makedirs(path,exist_ok=True)
            #print(fn)
            url = f"wget -O {fn} https://data.binance.vision/{fn}"
            print(url)
            os.system(url)
            #break
        break

def get_symbol_historical_list(symbol,period='1m'):
    import requests

    all_files = []
    nextMarker = ''
    while True:
        if not nextMarker:
            url = f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/daily/klines/{symbol}/{period}/"
        else:
            urlencoded = urllib.parse.quote(nextMarker)
            url = f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/daily/klines/{symbol}/{period}/&marker={ urlencoded}"
        print(url)
        r = requests.get(url)
        data = r.text
        data = data.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&apos;',"'").replace('&quot;','"')
        data = remove_xmlns(data)
        prefix = get_xml_node_multiple_text(data,'./Prefix')
        marker = get_xml_node_multiple_text(data,'./NextMarker')
        truncated = get_xml_node_multiple_text(data,'./IsTruncated')

        print(prefix,marker,truncated)
        files = get_xml_node_multiple_text(data, './/Key')
        # print(files)
        # print(len(files))

        all_files += files

        if truncated[0] == 'true' and marker:
            nextMarker = marker[0]
        else:
            break
    all_files = filter(lambda x: x.find('CHECKSUM') == -1, all_files)
    return all_files


def write_file(filename, data):
    with open(filename, 'w') as f:
        for item in data:
            f.write("%s\n" % item)


def remove_xmlns(xml):
    import re
    return re.sub(' xmlns="[^"]+"', '', xml, count=1)

def get_symbol_list(type='SPOT'):
    import requests
    url = f"https://api.binance.com/api/v3/exchangeInfo"
    r = requests.get(url)
    data = r.json()
    symbols = []
    for x in data['symbols']:
        if type in x['permissions']:
            symbols.append(x['symbol'])
    return symbols

def get_xml_node_multiple_text(xml, name):
    tree = ET.fromstring(xml)
    nodes = tree.findall(name)
    return [node.text for node in nodes]

def get_xml_node_text(xml, name):
    tree = ET.fromstring(xml)
    node = tree.find(name)
    if not node:
        return ''
    return node.text

def sync_symbol_info(name='SPOT', period = '1m'):

    symbols = get_symbol_list(name)
    f = open(f"symbols_{name}.txt", "w")
    for symbol in symbols:
        f.write(f"{symbol}\n")
    for symbol in get_symbol_list():
        all_files = get_symbol_historical_list(symbol,period)
        os.makedirs(f"tasks/{name}/{period}", exist_ok=True)
        write_file(f"tasks/{name}/{period}/{symbol}_want.txt", all_files)


def sync_symbol_data(name='SPOT', period = '1m'):
    for file in os.listdir(f"tasks/{name}/{period}"):
        if not file.endswith("_want.txt"):
            continue
        fn = os.path.join(f"tasks/{name}/{period}", file)
        print(f"{fn}")
        fin_list = []
        fn_fin = f"{fn.replace('_want.txt','')}_fin.txt"
        if os.path.exists(fn_fin):
            fin_list = open(fn_fin).readlines()
            fin_list = [x.strip() for x in fin_list]

        for line in open(fn).readlines():
            line = line.strip()
            if not line :
                continue

            if line  in fin_list: # skip if file is not in fin_list
                continue

            if os.path.exists(line) and os.path.getsize(line) > 0: # skip if file exists
                continue

            path, f = os.path.split(line)
            os.makedirs(path, exist_ok=True)
            url = f"wget -c -O {line} https://data.binance.vision/{line}"
            print(url)
            os.system(url)
            with open(fn_fin, 'a') as f:
                f.write(f"{line}\n")

# get date list from start to after days
def get_date_list(start,days=1):
    import datetime
    today = start.date()
    date_list = [today - datetime.timedelta(days=x) for x in range(days)]
    return date_list

def sync_recent_days_for_symbol(symbol,name='SPOT',period = '1m',days=1):
    date_list = get_date_list(datetime.datetime.now(),days)
    for date in date_list:
        fn = f"data/spot/daily/klines/{symbol}/{period}/{symbol}-{period}-{str(date).split(' ')[0]}.zip"
        print(fn)
        fin_fn = f"tasks/{name}/{period}/{symbol}_fin.txt"
        path, f = os.path.split()

        os.makedirs(path, exist_ok=True)
        url = f"wget -c -O {fn} https://data.binance.vision/{fn}"
        print(url)
        os.system(url)
        with open(fin_fn, 'a') as f:
            f.write(f"{fn}\n")

# sync_recent_days_for_symbol('BTCUSDT',days=10)

def sync_recent_days(name='SPOT',period = '1m',days=2):
    lines = open(f"symbols_{name}.txt").readlines()
    for symbol in [x.strip() for x in lines]:
        print(f"Syncing {symbol}")
        sync_recent_days_for_symbol(symbol,name,period)

if __name__ == "__main__":
    fire.Fire()
    # sync_symbol_info()
    # sync_symbol_data()