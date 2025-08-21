# MCP 测试工具

支持stdio/sse/streamable

类似MCP官方的 inspector 的命令行版本

# 安装

安装python3 和 pip 环境

# 命令行参考

type参数：MCP类型
- sse : sse 类型
- http: streamable http类型
- stdio: stdio类型 

命令行参数示例
```
any_client.py -type sse -url http://your.com/sse
any_client.py -type http -url http://your.com/mcp
any_client.py -type stdio -url "npx -y @modelcontextprotocol/server-sequential-thinking"
```

如果不提供命令行参数直接运行，会提示输入url

# 命令行操作

1. 输入url后，如果连接成功，会列出工具清单

2. 输入数字 1~n 会进入工具，会展示工具说明书

3. 此时输入json格式的参数，来测试这个工具。建议从外界记事本写好json复制粘贴进来。需要保证是一个合法的json格式。

# 支持的其他命令

- list: 列出工具清单
- dump: 保存全局工具完整说明书到当前目录的  schema.json 文件



