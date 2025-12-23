"""版本检测服务

提供版本检测功能，通过GitHub API检查是否有新版本可用。
"""
import os
import re
import logging
import urllib.request
import urllib.error
import json

logger = logging.getLogger(__name__)

# 当前版本号
CURRENT_VERSION = '2.1.0'

# GitHub仓库信息（可通过环境变量配置）
GITHUB_OWNER = os.getenv('GITHUB_OWNER', 'mansdeanna2-collab')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'server-manager')

# GitHub API超时时间（秒）
GITHUB_API_TIMEOUT = int(os.getenv('GITHUB_API_TIMEOUT', '10'))


def parse_version(version_str: str) -> tuple:
    """解析版本号字符串为可比较的元组

    Args:
        version_str: 版本号字符串，如 'v2.1.0' 或 '2.1.0'

    Returns:
        版本号元组，如 (2, 1, 0)
    """
    # 移除 'v' 前缀（如果有）
    version_str = version_str.lstrip('vV')

    # 使用正则表达式提取数字部分
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return tuple(int(x) for x in match.groups())

    # 如果无法解析，返回 (0, 0, 0)
    return (0, 0, 0)


def compare_versions(version1: str, version2: str) -> int:
    """比较两个版本号

    Args:
        version1: 第一个版本号
        version2: 第二个版本号

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def get_current_version() -> str:
    """获取当前版本号

    Returns:
        当前版本号字符串
    """
    return CURRENT_VERSION


def check_for_updates() -> dict:
    """检查是否有新版本可用

    通过GitHub API检查最新发布版本，并与当前版本进行比较。

    Returns:
        dict: 包含以下字段:
            - success: 是否成功检查
            - current_version: 当前版本号
            - latest_version: 最新版本号（如果成功）
            - has_update: 是否有更新可用
            - release_url: 发布页面URL（如果有更新）
            - release_notes: 发布说明（如果有更新）
            - published_at: 发布时间（如果有更新）
            - message: 结果信息
    """
    result = {
        'success': False,
        'current_version': CURRENT_VERSION,
        'latest_version': None,
        'has_update': False,
        'release_url': None,
        'release_notes': None,
        'published_at': None,
        'message': ''
    }

    try:
        # 构建GitHub API URL
        api_url = f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest'

        # 创建请求
        req = urllib.request.Request(
            api_url,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'ServerManager/{CURRENT_VERSION}'
            }
        )

        # 发送请求
        with urllib.request.urlopen(req, timeout=GITHUB_API_TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))

        # 解析响应
        latest_version = data.get('tag_name', '')
        result['latest_version'] = latest_version.lstrip('vV')
        result['release_url'] = data.get('html_url', '')
        result['release_notes'] = data.get('body', '')
        result['published_at'] = data.get('published_at', '')

        # 比较版本
        comparison = compare_versions(CURRENT_VERSION, latest_version)
        result['has_update'] = comparison < 0

        if result['has_update']:
            result['message'] = f'发现新版本 {result["latest_version"]}，当前版本 {CURRENT_VERSION}'
        else:
            result['message'] = f'当前版本 {CURRENT_VERSION} 已是最新版本'

        result['success'] = True
        logger.info(f"Version check completed: {result['message']}")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 没有发布版本 - 这不是一个错误，只是没有发布版本
            # 返回 success=True 因为检查本身成功了，只是没有发布
            result['message'] = '暂无发布版本信息，无法检查更新'
            result['success'] = True
            result['has_update'] = False
            result['latest_version'] = CURRENT_VERSION  # 设置为当前版本表示没有更新
            logger.info("No releases found on GitHub - repository may not have published releases")
        else:
            result['message'] = f'检查更新失败: HTTP {e.code}'
            result['success'] = False
            logger.error(f"HTTP error checking for updates: {e.code}")
    except urllib.error.URLError as e:
        result['message'] = f'网络错误: {str(e.reason)}'
        result['success'] = False
        logger.error(f"URL error checking for updates: {e.reason}")
    except json.JSONDecodeError as e:
        result['message'] = '解析版本信息失败'
        result['success'] = False
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
        result['message'] = f'检查更新时发生错误: {str(e)}'
        result['success'] = False
        logger.error(f"Error checking for updates: {e}")

    return result


def get_version_info() -> dict:
    """获取完整的版本信息

    Returns:
        dict: 包含版本信息
    """
    return {
        'current_version': CURRENT_VERSION,
        'github_owner': GITHUB_OWNER,
        'github_repo': GITHUB_REPO,
        'github_url': f'https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}'
    }
