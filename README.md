
## binance 交易所历史行情数据下载 

#### symbol 信息查询
从 binance 数据网站页面分析 js 加载过程发现，其查询 aws 的数据记录了，通过循环翻页形式获取数据
python程序 "klinedata.py" 通过分析网页源码，获取数据记录的 aws 地址，然后通过循环翻页的方式获取数据,记录合约清单到本地文件 "symbol_SPOT.txt",
'sync_symbol_info()' 查询symbol历史数据记录，写入 'tasks/SPOT/1m/xxx_want.txt' 文件 。 

#### symbol 历史数据下载 
读取指定symbol历史记录文件 'xxx_want.txt', 使用wget进行下载，并记录成功下载的文件记录到 'xxx_fin.txt' 文件中。以便下次下载时，跳过已经下载的文件。

#### symbol 近期数据下载
1. "symbol_SPOT.txt" 文件中记录了所有的合约信息，构建指定日期的下载url，并通过wget下载，记录下载成功的文件到 'xxx_fin.txt' 文件中。以便下次下载时，跳过已经下载的文件。
2. 近期数据选择近2天的数据下载，防止数据不完整，导致数据不准确。

#### 新上架symbol 处理 
1. sync_symbol_info()  定期执行，生成新的 'symbol_SPOT.txt' 文件


### run it !

> python ./kline_sync.py sync_symbol_info 'SPOT' '1m'
>
> python ./kline_sync.py sync_symbol_data 'SPOT' '1m'
