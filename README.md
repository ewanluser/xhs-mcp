# 小红书MCP服务
[![smithery badge](https://smithery.ai/badge/@jobsonlook/xhs-mcp)](https://smithery.ai/server/@jobsonlook/xhs-mcp)
## 特点
- [x] 采用js逆向出x-s,x-t,直接请求http接口,无须笨重的playwright
- [x] 支持CookieCloud自动同步Cookie
- [x] 搜索笔记
- [x] 获取笔记内容
- [x] 获取笔记的评论
- [x] 发表评论

![特性](https://raw.githubusercontent.com/jobsonlook/xhs-mcp/master/docs/feature.png)

## 快速开始

### 1. 环境
 * node
 * python 3.12
 * uv (pip install uv)

### 2. 安装依赖
```sh

git clone git@github.com:jobsonlook/xhs-mcp.git

cd xhs-mcp
uv sync 

```

### 3. 获取小红书的cookie

#### 方法一：使用CookieCloud（推荐）
1. 安装并配置[CookieCloud](https://github.com/easychen/CookieCloud)
2. 在浏览器中安装CookieCloud扩展
3. 登录小红书网站，CookieCloud会自动同步cookie
4. 在第4步的配置中使用CookieCloud相关环境变量

#### 方法二：手动获取cookie
[打开web小红书](https://www.xiaohongshu.com/explore)
登录后，获取cookie，将cookie配置到第4步的 XHS_COOKIE 环境变量中
![cookie](https://raw.githubusercontent.com/jobsonlook/xhs-mcp/master/docs/cookie.png)

### 4. 配置mcp server

#### 使用CookieCloud配置
```json
{
    "mcpServers": {
        "xhs-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/Users/xxx/xhs-mcp",
                "run",
                "main.py"
            ],
            "env": {
                "COOKIE_CLOUD_URL": "http://your-cookiecloud-server.com",
                "COOKIE_CLOUD_UUID": "your-uuid",
                "COOKIE_CLOUD_PASSWORD": "your-password"
            }
        }
    }
}
```

#### 使用手动Cookie配置
```json
{
    "mcpServers": {
        "xhs-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/Users/xxx/xhs-mcp",
                "run",
                "main.py"
            ],
            "env": {
                "XHS_COOKIE": "xxxx"
            }
        }
    }
}
```

## 免责声明
本项目仅用于学习交流，禁止用于其他用途，任何涉及商业盈利目的均不得使用，否则风险自负。

