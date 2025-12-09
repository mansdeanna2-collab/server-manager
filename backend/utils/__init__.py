from datetime import datetime, timezone, timedelta


# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))


def china_now():
    """获取中国当前时间（东八区）"""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)
