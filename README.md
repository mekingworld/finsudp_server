# INS/UDP to C-MODE Converter
## 项目介绍
FINS/UDP to C-MODE Converter 是一个用于工业自动化通信的协议转换工具。它能够将FINS/UDP协议数据包转换为C-MODE协议格式，并通过串口发送到设备，同时将设备返回的C-MODE协议响应转换回FINS/UDP格式发送给客户端。

该工具提供了友好的图形用户界面，支持多客户端同时通信，适用于工业控制系统中不同协议设备之间的通信桥梁。

## 功能特点
- 支持FINS/UDP到C-MODE协议的双向转换
- 多客户端通信支持（使用队列管理客户端地址）
- 串口参数可配置（波特率、数据位、停止位、校验位）
- UDP服务器参数可配置（IP地址、端口）
- 实时通信日志显示与管理
- 支持多线程处理，避免通信阻塞
- 友好的图形用户界面
## 系统要求
- Windows操作系统
- Python 3.6+（推荐Python 3.10+）
- 支持的串口设备
- 网络连接（用于UDP通信）
## 安装指南
1. 克隆或下载项目到本地
```
git clone https://github.com/
yourusername/
finsudp-cmode-converter.git
cd finsudp-cmode-converter
```
2. 安装依赖包
```
pip install -r requirements.
txt
```
依赖包包括：

- pyserial==3.5：用于串口通信
- tkinter==8.6：用于图形用户界面
## 使用方法
1. 运行程序
```
python finsudp_server.py
```
2. 配置串口参数
   
   - 选择可用串口
   - 设置波特率（默认9600）
   - 设置数据位（默认8）
   - 设置停止位（默认1）
   - 设置校验位（默认无）
3. 配置UDP服务器参数
   
   - 设置监听IP地址（默认0.0.0.0，监听所有接口）
   - 设置监听端口（默认9600）
4. 点击"启动服务器"按钮开始运行
5. 服务器运行后，可以在日志区域查看通信记录
6. 点击"停止服务器"按钮停止运行
## 协议转换说明
### FINS/UDP 到 C-MODE
1. 解析FINS/UDP数据包，提取命令类型、内存区域、地址、数据等信息
2. 根据命令类型构建相应的C-MODE命令帧
3. 计算C-MODE命令的校验和并添加到命令帧
4. 通过串口发送C-MODE命令到设备
### C-MODE 到 FINS/UDP
1. 从串口接收C-MODE响应数据
2. 解析C-MODE响应，提取命令类型、错误码、数据等信息
3. 构建FINS/UDP响应数据包
4. 从客户端队列中获取对应的客户端地址
5. 发送FINS/UDP响应到客户端
## 代码结构
- finsudp_server.py ：主程序文件，包含以下主要部分：
  
  - FINS_UDP_Server 类：主应用类，包含UI创建、串口和UDP服务器管理
  - data_processor 方法：合并UDP和串口监听处理逻辑
  - fins_to_cmode 方法：FINS/UDP到C-MODE协议转换
  - cmode_to_fins 方法：C-MODE到FINS/UDP协议转换
  - calculate_fcs 方法：计算校验和
- requirements.txt ：项目依赖包列表
## 注意事项
1. 确保串口设备已正确连接并安装驱动
2. 运行前请检查防火墙设置，确保UDP端口已开放
3. 多客户端通信时，请注意网络带宽和设备响应时间
4. 如遇到通信问题，请查看日志区域的错误信息
5. 程序运行时请不要关闭串口或断开网络连接
## 联系方式
如有问题或建议，请联系：

- Email: your.email@example.com
- GitHub: https://github.com/yourusername
© 2023 FINS/UDP to C-MODE Converter. All rights reserved.