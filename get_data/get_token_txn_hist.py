from initialize_data import *


def main(protocol, address, offset):
    txns_timestamps = get_token_history(address, offset)
    txns_timestamps_sum = txns_timestamps.groupby('timeStamp').count().reset_index()
    txns_timestamps_sum['protocol'] = protocol
    txns_timestamps_sum.columns = ['date', 'count', 'protocol']
    txns_timestamps_sum = txns_timestamps_sum[['protocol', 'date', 'count']]
    txns_timestamps_sum = txns_timestamps_sum[txns_timestamps_sum.date == txns_timestamps_sum.date.max()]
    print txns_timestamps_sum
    insert_db_today(txns_timestamps_sum, 'token_txn_hist')


main('Numeraire', '0x1776e1F26f98b1A5dF9cD347953a26dd3Cb46671', 1)
