# vrchat[^vrc]-osc-platform

> [!Important]
> 本项目仍在 Beta 阶段, 切勿在生产环境使用

## 项目简介
本项目为 [VRChat OSC](https://docs.vrchat.com/docs/osc-overview) 服务提供了一个框架, 可以以插件的方式调用 OSC API


## 目录结构
|      文件(夹)       |                                    描述                                     |                 结构                 |
|:----------------:|:-------------------------------------------------------------------------:|:----------------------------------:|
|     plugins/     |                               插件目录, 会引入每个模块                               |          与 Python 包相同或相似           |
|       src/       |                           源码目录, `main.py` 为入口文件                           |            Python 项目结构             |
|      logs/       |                               (未上传) 日志文件文件夹                               | 每个日志文件以如下格式命名 `<date>[.error].log` |
| requirements.txt | 依赖, 类似于 `package.json` 的 deps, 可使用 `pip install -r requirements.txt` 安装依赖 |        与 `pip freeze` 相同或相似        |


## 环境部署
1. 需求 Python 3.11 及以上版本
2. 使用 git 或 GH CLI 克隆当前存储库 main 分支, 在终端中运行如下指令 (以 git 为例):
   ```shell
   git clone https://github.com/Lovemilk-Inc/vrchat-osc-platform.git
   ```
3. 将工作路径切换到克隆的目录, 在默认配置下可以在终端中运行如下指令:
   ```shell
   cd ./vrchat-osc-platform
   ```
4. 创建 Python 虚拟环境 (如果有多个 Python 可能需要自行选择相应环境), 一般地可以在终端中运行如下指令: <br>
   ```shell
   python -m venv ./venv
   ```
5. 激活虚拟环境 ~~激活虚拟环境, 转到设置以激活虚拟环境~~
   1. 在 Windows 上, 可以在终端中运行:
      ```shell
      ./venv/Scripts/activate
      ```
      > 如果您的 Powershell 提示无法运行 PS1 脚本, 请参阅 [此处](https://learn.microsoft.com/zh-cn/powershell/module/microsoft.powershell.core/about/about_scripts?view=powershell-7.4#how-to-run-a-script)
      以解决, 并重新运行上述脚本
   2. 在 *nix (Unix 和 Unix-like) 可以在终端中运行: 
      ```shell
      source ./venv/bin/activate
      ```
   
6. 安装依赖, 在已激活虚拟环境的终端中运行如下指令:
   ```shell
   pip install -r ./requirements.txt
   ```
7. 运行 `src/main.py`, 使用如下命令运行:
   ```shell
   python src/main.py
   ```

## 版权信息
[^vrc]: [VRChat](https://vrchat.com) 为 VRChat Inc. 的商标
