from typing import Any, List, Dict, Optional
import asyncio
import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP, Context

from api.xhs_api import XhsApi
import logging
from urllib.parse import urlparse, parse_qs
from PyCookieCloud import PyCookieCloud

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP("小红书", port=8809)

def get_cookie_from_cookiecloud():
    """Fetches cookies from CookieCloud and formats them into a string."""
    cookie_cloud_url = os.getenv('COOKIE_CLOUD_URL')
    cookie_cloud_uuid = os.getenv('COOKIE_CLOUD_UUID')
    cookie_cloud_password = os.getenv('COOKIE_CLOUD_PASSWORD')
    logger.info(f'cookie_cloud_url:{cookie_cloud_url}')
    logger.info(f'cookie_cloud_uuid:{cookie_cloud_uuid}')
    logger.info(f'cookie_cloud_password:{cookie_cloud_password}')

    if not all([cookie_cloud_url, cookie_cloud_uuid, cookie_cloud_password]):
        logger.info("CookieCloud credentials not fully provided, falling back to XHS_COOKIE env var.")
        return None

    try:
        cookie_cloud = PyCookieCloud(cookie_cloud_url, cookie_cloud_uuid, cookie_cloud_password) # type: ignore
        
        if not cookie_cloud.get_the_key():
            logger.error('Failed to get the key from CookieCloud')
            return None
        if not cookie_cloud.get_encrypted_data():
            logger.error('Failed to get encrypted data from CookieCloud')
            return None
        
        decrypted_data = cookie_cloud.get_decrypted_data()
        decrypted_data = decrypted_data.get('xiaohongshu', [])
        #logger.info(f'decrypted_data:{decrypted_data}')
       
        if len(decrypted_data) > 0:
            xhs_cookies = [
                cookie for cookie in decrypted_data
                if cookie.get('domain') == '.xiaohongshu.com'
            ]
            if xhs_cookies:
                cookie_items = [f"{cookie['name']}={cookie['value']}" for cookie in xhs_cookies]
                return "; ".join(cookie_items)


     

    except Exception as e:
        logger.error(f"An error occurred while fetching cookies from CookieCloud: {e}", exc_info=True)
        return None
xhs_cookie = get_cookie_from_cookiecloud()
print(xhs_cookie)
if not xhs_cookie:
    xhs_cookie = os.getenv('XHS_COOKIE')
if not xhs_cookie:
    logger.error("XHS_COOKIE not found. Please set XHS_COOKIE environment variable or configure CookieCloud.")

xhs_api = XhsApi(cookie=xhs_cookie)


def get_nodeid_token(url=None, note_ids=None):
    if note_ids is not None:
        note_id = note_ids[0,24]
        xsec_token = note_ids[24:]
        return {"note_id": note_id, "xsec_token": xsec_token}
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    note_id = parsed_url.path.split('/')[-1]
    xsec_token = None
    xsec_token_list = query_params.get('xsec_token', []) # type: ignore
    if len(xsec_token_list) > 0:
        xsec_token = xsec_token_list[0]
    return {"note_id": note_id, "xsec_token": xsec_token}


@mcp.tool()
async def check_cookie() -> str:
    """检测cookie是否失效

    """
    try:
        if xhs_api._cookie is None:
            xhs_cookie = get_cookie_from_cookiecloud()
            xhs_api._cookie = xhs_cookie
            logger.info(f'xhs_cookie:{xhs_api._cookie}')
        data = await xhs_api.get_me()

        if 'success' in data and data['success'] == True:
            return "cookie有效"
        else:
            return "cookie已失效"
    except Exception as e:
        logger.error(e)
        return "cookie已失效"



@mcp.tool()
async def home_feed() -> str:
    """获取首页推荐笔记

    """
    data = await xhs_api.home_feed()
    result = "搜索结果：\n\n"
    if 'data' in data and 'items' in data['data'] and len(data['data']['items']) > 0:
        for i in range(0, len(data['data']['items'])):
            item = data['data']['items'][i]
            if 'note_card' in item and 'display_title' in item['note_card']:
                title = item['note_card']['display_title']
                liked_count = item['note_card']['interact_info']['liked_count']
                # cover=item['note_card']['cover']['url_default']
                url = f'https://www.xiaohongshu.com/explore/{item["id"]}?xsec_token={item["xsec_token"]}'
                result += f"{i}. {title}  \n 点赞数:{liked_count} \n   链接: {url}  \n\n"
    else:
        result = await check_cookie()
        if "有效" in result:
            result = f"未找到相关的笔记"
    return result

@mcp.tool()
async def search_notes(keywords: str,page: int = 1,limit: int = 20) -> str:
    """根据关键词搜索笔记

        Args:
            keywords: 搜索关键词
    """

    data = await xhs_api.search_notes(keywords,page=page,limit=limit)
    logger.info(f'keywords:{keywords},page:{page},limit:{limit},data:{data}')
    result = "搜索结果：\n\n"
    if 'data' in data and 'items' in data['data'] and len(data['data']['items']) > 0:
        for i in range(0, len(data['data']['items'])):
            item = data['data']['items'][i]
            if 'note_card' in item and 'display_title' in item['note_card']:
                title = item['note_card']['display_title']
                liked_count = item['note_card']['interact_info']['liked_count']
                # cover=item['note_card']['cover']['url_default']
                url = f'https://www.xiaohongshu.com/explore/{item["id"]}?xsec_token={item["xsec_token"]}'
                result += f"{i}. {title}  \n 点赞数:{liked_count} \n   链接: {url}  \n\n"
    else:
        result = await check_cookie()
        if "有效" in result:
            result = f"未找到与\"{keywords}\"相关的笔记"
    return result


@mcp.tool()
async def get_note_content(url: str) -> str:
    """获取笔记内容,参数url要带上xsec_token

    Args:
        url: 笔记 url
    """
    params = get_nodeid_token(url=url)
    data = await xhs_api.get_note_content(**params)
    logger.info(f'url:{url},data:{data}')
    result = ""
    if 'data' in data and 'items' in data['data'] and len(data['data']['items']) > 0:
        for i in range(0, len(data['data']['items'])):
            item = data['data']['items'][i]

            if 'note_card' in item and 'user' in item['note_card']:
                note_card = item['note_card']
                cover = ''
                if 'image_list' in note_card and len(note_card['image_list']) > 0 and note_card['image_list'][0][
                    'url_pre']:
                    cover = note_card['image_list'][0]['url_pre']

                data_format = datetime.fromtimestamp(note_card.get('time', 0) / 1000)
                liked_count = item['note_card']['interact_info']['liked_count']
                comment_count = item['note_card']['interact_info']['comment_count']
                collected_count = item['note_card']['interact_info']['collected_count']

                url = f'https://www.xiaohongshu.com/explore/{params["note_id"]}?xsec_token={params["xsec_token"]}'
                result = f"标题: {note_card.get('title', '')}\n"
                result += f"作者: {note_card['user'].get('nickname', '')}\n"
                result += f"发布时间: {data_format}\n"
                result += f"点赞数: {liked_count}\n"
                result += f"评论数: {comment_count}\n"
                result += f"收藏数: {collected_count}\n"
                result += f"链接: {url}\n\n"
                result += f"内容:\n{note_card.get('desc', '')}\n"
                result += f"封面:\n{cover}"

            break
    else:
        result = await check_cookie()
        if "有效" in result:
            result = "获取失败"
    return result


@mcp.tool()
async def get_note_comments(url: str, cursor: str = "", top_comment_id: str = "", fetch_all: bool = False) -> str:
    """获取笔记评论,参数url要带上xsec_token

    Args:
        url: 笔记 url
        cursor: 评论游标，用于分页
        top_comment_id: 顶层评论ID，用于获取该评论下的回复
        fetch_all: 是否获取所有评论页面
    

    """
    params = get_nodeid_token(url=url)
    all_comments = []
    current_cursor = cursor
    page_num = 1
    
    while True:
        params['cursor'] = current_cursor
        params['top_comment_id'] = top_comment_id

        data = await xhs_api.get_note_comments(**params)
        logger.info(f'url:{url},cursor:{current_cursor},page:{page_num},data:{len(data["data"]["comments"])}')

        if 'data' in data and 'comments' in data['data'] and len(data['data']['comments']) > 0:
            all_comments.extend(data['data']['comments'])
        
        # Check if there are more comments
        if not fetch_all or not data.get('data', {}).get('has_more', False):
            break
            
        # Get cursor for next page
        current_cursor = data.get('data', {}).get('cursor', '')
        if not current_cursor:
            break
            
        page_num += 1
        
        # Safety limit to prevent infinite loops
        if page_num > 10:
            break

    result = ""
    logger.info(f'all_comments:{len(all_comments)}')
    if all_comments:
        for i, item in enumerate(all_comments):
            data_format = datetime.fromtimestamp(item['create_time'] / 1000)

            result += f"id: {item['id']}\n{i}. {item['user_info']['nickname']}（{data_format}）: {item['content']}\n"

            if 'sub_comments' in item and item['sub_comments']:
                for sub_item in item['sub_comments']:
                    sub_data_format = datetime.fromtimestamp(sub_item['create_time'] / 1000)
                    nickname = sub_item.get('user_info', {}).get('nickname', '')
                    content = sub_item.get('content', '')
                    target_user = ""
                    target_comment = sub_item.get('target_comment')
                    if target_comment:
                        target_info = target_comment.get('user_info')
                        if target_info and target_info.get('nickname'):
                            target_user = f" 回复 @{target_info['nickname']}"

                    result += f"    - {nickname}{target_user} ({sub_data_format}): {content}\n"
            result += "\n"

    else:
        result = await check_cookie()
        if "有效" in result:
            result = "暂无评论"

    # Add pagination info
    if 'data' in data:
        if data['data'].get('has_more', False):
            next_cursor = data['data'].get('cursor', '')
            if next_cursor:
                result += f"\n\n下一页评论游标: {next_cursor}"
        result += f"\n总共获取了 {len(all_comments)} 条评论"

    return result


@mcp.tool()
async def post_comment(comment: str, note_id: str) -> str:
    """发布评论到指定笔记

    Args:
        note_id: 笔记 note_id
        comment: 要发布的评论内容
    """
    # params = get_nodeid_token(url)
    response = await xhs_api.post_comment(note_id, comment)
    if 'success' in response and response['success'] == True:
        return "回复成功"
    else:
        result = await check_cookie()
        if "有效" in result:
            return "回复失败"
        else:
            return result


if __name__ == "__main__":
    logger.info("mcp run")
    mcp.run(transport='stdio')
