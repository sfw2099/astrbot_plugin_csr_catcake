# 星穹铁道猫猫糕查询

[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/sfw2099/astrbot_plugin_csr_catcake)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

AstrBot 插件：根据服务器和猫猫糕/角色名查询其他玩家登记的猫猫糕，返回 UID 及猫猫糕/尾巴图片。

数据来源：[猫猫糕友人帐](https://catcake.hoshimi.io/)

## 安装

在 AstrBot WebUI 插件市场搜索 `astrbot_plugin_csr_catcake` 安装。

## 使用说明

### 指令

```
/找猫糕 <服务器> <角色名/猫猫糕名>
```

### 示例

| 指令 | 说明 |
|------|------|
| `/找猫糕 官服 糯米团` | 查询官服中登记糯米团的玩家 |
| `/找猫糕 官服 丹恒` | 输入角色名自动映射为糯米团 |
| `/找猫糕 B服 姬子` | 查询B服中登记星辰拿铁(姬子)的玩家 |
| `/找猫糕 全部 阿基维利` | 跨服查询今日限定阿基喵利 |
| `/找猫糕 垃圾糕` | 使用默认服务器查询 |

### 服务器支持

官服 / B服 / 亚服 / 美服 / 欧服 / 港澳台 / 其他 / 全部

### 查询结果

每查到一个玩家，将返回：
- 玩家名 + UID + 所在服务器
- 该玩家登记的所有猫猫糕
- 猫猫糕图片 + 尾巴图片（可在配置中关闭）

### 阿基喵利

阿基喵利为今日限定猫猫糕，每天凌晨 4:00 自动清除。查询时会标注 `[今日限定]`。

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| default_server | string | 官服 | 未指定服务器时的默认服务器 |
| default_limit | int | 3 | 每次查询最多返回的记录数 |
| send_images | bool | true | 是否发送猫猫糕/尾巴图片 |

## 数据来源

数据来自 [猫猫糕友人帐](https://catcake.hoshimi.io/) 公开 API，每周一凌晨 4:00 重置。

## License

MIT