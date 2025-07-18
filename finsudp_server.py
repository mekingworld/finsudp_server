import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import socket
import threading
import queue
import time
import logging
from datetime import datetime

class FINS_UDP_Server:
    def __init__(self, root):
        self.root = root
        self.root.title("FINS/UDP to C-MODE Converter")
        self.root.geometry("800x600")
        
        # 初始化变量
        self.serial_port = None
        self.udp_socket = None
        self.running = False
        self.log_queue = queue.Queue()
        self.client_queue = queue.Queue()  # 存储客户端地址队列
        self.last_client = None  # 存储最后通信的客户端地址
        
        # 创建UI
        self.create_widgets()
        
        # 启动日志处理线程
        self.log_thread = threading.Thread(target=self.process_log_queue, daemon=True)
        self.log_thread.start()
        
        # 填充可用串口
        self.refresh_ports()
        
        # 更新日志显示
        self.root.after(100, self.update_log_display)

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 串口设置区域
        serial_frame = ttk.LabelFrame(main_frame, text="串口设置", padding="5")
        serial_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(serial_frame, text="串口:").grid(row=0, column=0, sticky="w")
        self.port_combo = ttk.Combobox(serial_frame, width=15)
        self.port_combo.grid(row=0, column=1, padx=5)
        
        ttk.Button(serial_frame, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        
        ttk.Label(serial_frame, text="波特率:").grid(row=1, column=0, sticky="w")
        self.baud_combo = ttk.Combobox(serial_frame, width=10, values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.set("9600")
        self.baud_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(serial_frame, text="数据位:").grid(row=2, column=0, sticky="w")
        self.data_bits_combo = ttk.Combobox(serial_frame, width=5, values=["5", "6", "7", "8"])
        self.data_bits_combo.set("8")
        self.data_bits_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(serial_frame, text="停止位:").grid(row=3, column=0, sticky="w")
        self.stop_bits_combo = ttk.Combobox(serial_frame, width=5, values=["1", "1.5", "2"])
        self.stop_bits_combo.set("1")
        self.stop_bits_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(serial_frame, text="校验位:").grid(row=4, column=0, sticky="w")
        self.parity_combo = ttk.Combobox(serial_frame, width=5, values=["无", "奇", "偶"])
        self.parity_combo.set("无")
        self.parity_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # 服务器设置区域
        server_frame = ttk.LabelFrame(main_frame, text="UDP服务器设置", padding="5")
        server_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(server_frame, text="监听IP:").grid(row=0, column=0, sticky="w")
        self.ip_entry = ttk.Entry(server_frame, width=15)
        self.ip_entry.insert(0, "0.0.0.0")  # 监听所有接口
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(server_frame, text="监听端口:").grid(row=1, column=0, sticky="w")
        self.port_entry = ttk.Entry(server_frame, width=10)
        self.port_entry.insert(0, "9600")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 状态信息
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="服务器未启动")
        self.status_label.pack(pady=5)
        
        # 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="启动服务器", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(button_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="通信日志", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, width=90, height=15, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        clear_btn = ttk.Button(log_frame, text="清除日志", command=self.clear_log)
        clear_btn.pack(pady=5)
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.log_queue.put(log_entry)

    def process_log_queue(self):
        while True:
            try:
                log_entry = self.log_queue.get(timeout=0.1)
                if self.log_area:
                    self.log_area.configure(state=tk.NORMAL)
                    self.log_area.insert(tk.END, log_entry + "\n")
                    self.log_area.configure(state=tk.DISABLED)
                    self.log_area.see(tk.END)
            except queue.Empty:
                pass
            time.sleep(0.1)

    def update_log_display(self):
        while not self.log_queue.empty():
            log_entry = self.log_queue.get()
            if self.log_area:
                self.log_area.configure(state=tk.NORMAL)
                self.log_area.insert(tk.END, log_entry + "\n")
                self.log_area.configure(state=tk.DISABLED)
                self.log_area.see(tk.END)
        self.root.after(100, self.update_log_display)

    def clear_log(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state=tk.DISABLED)
        self.log_message("日志已清除")

    def start_server(self):
        # 获取串口参数
        port = self.port_combo.get()
        baud = int(self.baud_combo.get())
        data_bits = int(self.data_bits_combo.get())
        stop_bits = float(self.stop_bits_combo.get())
        
        parity_map = {"无": serial.PARITY_NONE, "奇": serial.PARITY_ODD, "偶": serial.PARITY_EVEN}
        parity = parity_map.get(self.parity_combo.get(), serial.PARITY_NONE)
        
        # 获取服务器参数
        local_ip = self.ip_entry.get()
        try:
            local_port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("错误", "端口号必须是有效整数")
            return
        
        # 验证输入
        if not port:
            messagebox.showerror("错误", "请选择串口")
            return
        
        try:
            # 初始化串口
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=1
            )
            self.log_message(f"串口已连接: {port} @ {baud}bps")
            
            # 初始化UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((local_ip, local_port))
            self.udp_socket.settimeout(1)
            self.log_message(f"UDP服务器启动: {local_ip}:{local_port}")
            
                        # 启动线程
            self.running = True
            self.processor_thread = threading.Thread(target=self.data_processor, daemon=True)
            self.processor_thread.start()
            
            # 更新UI状态
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"服务器运行中: {local_ip}:{local_port}")
            self.log_message("服务器已启动")
            
        except Exception as e:
            self.log_message(f"启动服务器失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动服务器失败: {str(e)}")
            self.stop_server()

    def stop_server(self):
        self.running = False
        
        # 关闭串口
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                self.log_message("串口已关闭")
            except:
                pass
        
        # 关闭UDP socket
        if self.udp_socket:
            try:
                self.udp_socket.close()
                self.log_message("UDP服务器已关闭")
            except:
                pass
        
        # 更新UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="服务器已停止")
        self.log_message("服务器已停止")
        self.last_client = None
    def data_processor(self):
        """合并UDP和串口监听处理逻辑"""
        while self.running:
            try:
                # 监听UDP数据
                try:
                    data, addr = self.udp_socket.recvfrom(4096)
                    client_node = data[7:8].hex()
                    server_node = data[4:5]
                    sid         = data[9:10]
                    server_ip =self.ip_entry.get().split('.')[-1]
                    if data:
                        self.log_message(f"收到UDP数据来自 {addr}: {data.hex().upper()}")
                        # 判断是否是FINS/UDP协议
                        self.client_queue.put(addr)
                        if data[0] == 0x80 and len(data) > 4 and data[4] == int(server_ip):
                            # 转换FINS/UDP为C-MODE协议
                            cmode_data = self.fins_to_cmode(data)
                            self.log_message(cmode_data)
                            # 通过串口发送到设备
                            if self.serial_port and self.serial_port.is_open:
                                self.serial_port.write(cmode_data)
                                self.log_message(f"发送C-MODE数据到串口设备: {cmode_data.hex()}")
                except socket.timeout:
                    pass
                except OSError as e:
                    if self.running:
                        self.log_message(f"UDP接收错误: {str(e)}", "ERROR")
                    break

                # 监听串口数据
                if self.serial_port and self.serial_port.is_open:
                    try:
                        self.serial_port.timeout = 1
                        data = self.serial_port.read_until(b'\r')
                        # 读取完毕后清除串口缓存
                        self.serial_port.flushInput()
                        if data:
                            self.log_message(f"串口 -> FINSTCP (原始): {data}")    
                                # 转换C-MODE响应为FINS/UDP
                            fins_data = self.cmode_to_fins(data,sid,client_node,server_node)
                            # 发送响应回客户端
                            if self.udp_socket and fins_data:
                                try:
                                        client_addr = self.client_queue.get_nowait()
                                        self.udp_socket.sendto(fins_data, client_addr)
                                        self.log_message(f"发送FINS数据到客户端 {client_addr}: {fins_data.hex()}")
                                except queue.Empty:
                                        self.log_message("没有等待的客户端请求，无法发送响应", "WARNING")
                    except serial.SerialException as e:
                        if self.running:
                            self.log_message(f"串口错误: {str(e)}", "ERROR")
                        break

            except Exception as e:
                if self.running:
                    self.log_message(f"数据处理错误: {str(e)}", "ERROR")
            time.sleep(0.01)  # 避免CPU占用过高
    def calculate_fcs(self, data):
            """计算异或校验码"""
            # 初始化XOR结果为0
            fcs = 0
            # 遍历字符串中的每个字符（大端顺序：从左到右）
            for char in data:
                # 获取字符的ASCII码值
                ascii_value = ord(char)
                # 执行XOR运算
                fcs ^= ascii_value
            hex_result = hex(fcs)
            str_result = hex_result[2:4]
            return  f"{fcs:02X}"
    def fins_to_cmode(self, fins_data):
        """转换FINS/UDP协议到C-MODE协议 (简化示例)"""
        # 这里包含实际协议转换逻辑
        try:
         
            # 以下保持现有通信命令解析流程
            # 读取数据包中并记录日志
            self.log_message(f"[DEBUG] 完整数据包: {fins_data.hex().upper()}")
            command_type = fins_data[10:12].hex().upper()
            sid         = fins_data[9:10].hex().upper()
            if len(fins_data) > 12:
                mem_area_code = fins_data[12]
                address_bytes = fins_data[13:16].hex().upper()
                read_number = fins_data[16:18].hex().upper()
                self.log_message(f"命令类型: {command_type} 内存区: {mem_area_code:02X} 地址: {address_bytes} 读取个数: {read_number} SID: {sid}")  
            else:
                self.log_message(f"命令类型: {command_type} SID: {sid}")  

            if command_type == '0101':  # 读取命令
                cmode_cmd = f"@00FA000000000{command_type}{mem_area_code:02X}{address_bytes}{read_number}"
            elif command_type == '0102':  # 写入命令
                data_value = fins_data[18:].hex().upper()
                cmode_cmd = f"@00FA000000000{command_type}{mem_area_code:02X}{address_bytes}{read_number}{data_value}"
            elif command_type == '0601':  # 写入命令
                cmode_cmd = f"@00FA000000000{command_type}"
            else:
                return None
            
            # 添加校验码
            checksum = self.calculate_fcs(cmode_cmd)
            full_cmd =bytes(cmode_cmd+checksum+'*\r',encoding='utf-8')
            return (full_cmd)
        except Exception as e:
            self.log_message(f"协议转换错误: {str(e)}")
            return None


    def cmode_to_fins(self, cmode_data,sid,client_node,server_node):
        """转换C-MODE协议到FINS/UDP协议"""
        try:
            start_index = cmode_data.find(b'@')
            payload = cmode_data[start_index+1:-4]
            self.log_message(f"[DEBUG] C-MODE payload: {payload}")

            # 解析命令类型
            command_type = payload[14:18]
            error_code = payload[18:22]
            if command_type == b'0101' or command_type == b'0601':  # 读取命令
                cmode_value = payload[22:]
                fins_response = (            
                     b'\xC0'                  # ICF  
                    +b'\x00'                  # RSV                       
                    +b'\x02'                  # GCT   
                    +b'\x00'                  # DNA
                    +bytes.fromhex(client_node)    # DA1
                    +b'\x00'                  # DA2
                    +b'\x00'                  # SNA
                    +server_node              # SA1
                    +b'\x00'                  # SA2
                    +sid                      # SID
                    +bytes.fromhex(command_type.decode('utf-8'))           #命令码
                    +bytes.fromhex(error_code.decode('utf-8'))             #错误码
                    +bytes.fromhex(cmode_value.decode('utf-8'))            #数据
                )
            elif command_type == b'0102':  # 写入命令
                fins_response = (
                     b'\xC0'                  # ICF  
                    +b'\x00'                  # RSV                       
                    +b'\x02'                  # GCT   
                    +b'\x00'                  # DNA
                    +bytes.fromhex(client_node)                 # DA1
                    +b'\x00'                  # DA2
                    +b'\x00'                  # SNA
                    +server_node                 # SA1
                    +b'\x00'                  # SA2
                    +sid                     # SID
                    +bytes.fromhex(command_type.decode('utf-8'))           #命令码
                    +bytes.fromhex(error_code.decode('utf-8'))             #错误码
                )
            else:
                self.log_message(f"未知命令类型: {command_type}", "WARNING")
                return None

            return fins_response
        except Exception as e:
            self.log_message(f"协议转换错误: {str(e)}")
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = FINS_UDP_Server(root)
    root.mainloop()