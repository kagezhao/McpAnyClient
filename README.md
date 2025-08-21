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




