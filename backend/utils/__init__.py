from datetime import datetime, timezone, timedelta


# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))


def china_now():
    """获取中国当前时间（东八区）

    返回naive datetime对象（无时区信息），因为SQLAlchemy/SQLite
    默认使用naive datetime存储。返回值表示中国标准时间。
    """
    return datetime.now(CHINA_TZ).replace(tzinfo=None)
