from datetime import datetime, timedelta


def get_time_delta(item_time):
    ret = datetime.strptime(item_time[0:19], '%Y-%m-%dT%H:%M:%S')
    if item_time[19] == '+':
        ret -= timedelta(hours=int(item_time[19:22]), minutes=int(item_time[23:]))
    elif item_time[19] == '-':
        ret += timedelta(hours=int(item_time[19:22]), minutes=int(item_time[23:]))
    ret += timedelta(hours=6)
    item_time_delta = datetime.strptime(f"{datetime.now():%Y-%m-%d %H:%M:%S}", '%Y-%m-%d %H:%M:%S') - ret
    if item_time_delta > timedelta(days=1):
        return str(item_time_delta)[:str(item_time_delta).find('day') - 1] + ' дней назад'
    elif item_time_delta > timedelta(hours=10):
        return str(item_time_delta)[:2] + ' часов назад'
    elif item_time_delta > timedelta(hours=1):
        return str(item_time_delta)[:1] + ' часов назад'
    else:
        returning_time = str(item_time_delta)[
                         str(item_time_delta).find(':') + 1:str(item_time_delta).find(':') + 3] + ' минут назад'
        if returning_time.startswith('0'):
            returning_time = returning_time[1:]
        return returning_time
