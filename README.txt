AGB_Hack 1.6 中文测试版

原版：Donnie Russell，2007；本地原ROM保持不变。
字库：Fusion Pixel 8px monospaced zh_hans，原生点阵，不缩放。
字库及组件许可见 licenses/。

运行方式：用 GBA 模拟器打开 output/ 内的 .gba。
START：接受随机姓名 / 打开物品菜单。
左右：切换物品、动作菜单；方向键选择。
A：空格 / 继续消息；B：选择；R：取消。
L：ASCII键盘选择器；方向选择字符，R输入并关闭。
帮助：输入问号（L打开选择器，从空格向下三次、向右一次、R输入）。

源码和补丁范围：
本发行包没有GBA源码，故从原ROM做ARM绘字hook及字符串补丁。
后续SDL/JS Hack源码仅用作行为参考，不能视为本GBA版本的源码。
translations/full_zh.json保存完整译文；compact_zh.json用于ROM。
短名称因固定缓冲限制作一致缩写，例如“蝠”“兽”“魔”。
职业名保留原英文首字母作为游戏逻辑ID，例如F战士、W巫师。
帮助、谣言、百科连续块保持原始NUL边界；其他文本迁移并修复指针。
原作者姓名、版权、随机专名、虚构卷轴咒文、ASCII指令键保留。

构建、运行和补丁校验记录将在 output/ 对应 .json 中保存。
未进行完整通关或英文旧存档兼容认证；建议为中文ROM新建独立存档。
本地研究产物，不包含对外发布授权声明。

最终验证：
中文启动、职业初始装备、背包、动作菜单、符号帮助已运行复核。
七组ASCII许愿（long sword、potion of healing、scroll of identify、
wand of wishing、+2 leather armor、2 daggers、ring of protection）
调用实际ROM解析函数，类型/数量与原版一致；调用后名称指针完整恢复。
独立进程载入本次测试SRAM并重启，恢复画面与保存前整帧像素一致。
未完成敌对战斗专项测试或完整通关，不视为所有随机事件均已验证。
ROM和BPS位于output/；BPS需要原版AGB_Hack.bin作为源文件。
