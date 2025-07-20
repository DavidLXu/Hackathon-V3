import serial                  # 导入串口通信库pyserial
import serial.tools.list_ports # 导入串口工具包，用于列出串口列表
import time                    # 导入时间模块，用于延时操作
import sys                     # 导入系统模块，用于程序退出

# 定义数据包的起始和结束标志位
HEADER = 0xFE
TAIL = 0x0E

def list_ports():
    """
    列出所有可用的串口设备
    返回值：串口设备列表（serial.tools.list_ports_common.ListPortInfo对象列表）
    """
    ports = list(serial.tools.list_ports.comports())  # 获取所有串口设备列表
    if not ports:
        print("No available serial ports found.")     # 如果没有找到串口，打印提示信息
        return None

    print("Available serial ports:")
    # 列出所有串口设备的名称和描述，方便用户选择
    for i, p in enumerate(ports):
        print(f"{i + 1}. {p.device} - {p.description}")
    return ports

def choose_port(ports):
    """
    让用户从串口列表中选择一个串口
    参数：ports - 串口设备列表
    返回值：用户选择的串口设备名（字符串）
    """
    while True:
        try:
            choice = int(input("Please choose a port by number: "))  # 用户输入端口编号
            if 1 <= choice <= len(ports):
                return ports[choice - 1].device                        # 返回对应的串口设备名
            else:
                print("Invalid choice. Please select a valid port number.")  # 输入编号不合法提示
        except ValueError:
            print("Invalid input. Please enter a number.")            # 输入无法转换为数字提示

def find_available_port():
    """
    查找可用串口并尝试打开连接
    返回值：成功打开的Serial对象，失败返回None
    """
    ports = list_ports()        # 获取串口列表
    if not ports:
        return None             # 如果没有串口，直接返回None

    chosen_port = choose_port(ports)  # 让用户选择串口
    try:
        # 尝试打开用户选择的串口，波特率9600，超时1秒
        ser = serial.Serial(chosen_port, baudrate=9600, timeout=1)
        print(f"Successfully connected to {chosen_port}")
        return ser
    except Exception as e:
        print(f"Unable to connect to {chosen_port}: {e}")  # 连接失败时输出错误信息
        return None

def encode_distance_packet(distance_mm):
    """
    根据输入的距离值，生成符合协议的数据包
    参数：distance_mm - 距离值，单位毫米
    返回值：bytes类型的数据包，格式为 [HEADER, 高8位, 低8位, TAIL]
    """
    # 限制距离值在0~65535范围内（16位无符号整数）
    distance = max(0, min(65535, int(distance_mm)))
    # 获取高8位和低8位
    high = (distance >> 8) & 0xFF
    low = distance & 0xFF
    # 返回完整数据包的字节序列
    return bytes([HEADER, high, low, TAIL])

def main():
    """
    主程序入口
    实现打开串口，发送距离数据包，并接收打印返回的数据
    """
    ser = find_available_port()  # 查找并连接串口
    if not ser:
        sys.exit(1)              # 如果连接失败，退出程序

    while True:
        try:
            user_input = input("Enter the target distance in mm (enter 'q' to quit): ").strip()
            if user_input.lower() == 'q':          # 用户输入q则退出程序
                print("Exiting the program.")
                break

            if not user_input.isdigit():            # 检查输入是否为数字
                print("Invalid input. Please enter a valid number.")
                continue

            distance = int(user_input)               # 转换成整数距离
            packet = encode_distance_packet(distance)  # 编码成数据包
            ser.write(packet)                        # 通过串口发送数据包
            print(f"Sent: {packet.hex().upper()}") # 打印发送的十六进制数据

            time.sleep(0.1)  # 延时等待设备响应

            # 如果串口接收缓冲区有数据，则循环读取
            while ser.in_waiting:
                response = ser.readline().decode(errors='ignore').strip()
                print(f"Response: {response}")

        except KeyboardInterrupt:
            print("\nManual interrupt. Exiting the program.")  # 捕获Ctrl+C中断，安全退出
            break
        except Exception as e:
            print(f"Error: {e}")    # 捕获其他异常，打印错误信息并退出
            break

    ser.close()                   # 关闭串口连接

if __name__ == "__main__":
    main()                        # 运行主程序s