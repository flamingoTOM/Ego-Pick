<img src="https://cdn.nlark.com/yuque/0/2024/jpeg/42882794/1717141799417-93603f9f-64a1-47d0-9438-be89d873d53a.jpeg" width="386" title="" crop="0,0,1,1" id="ub630a8bc" class="ne-image">

产品规格书 :SPECIFICATION

型号：JY-ME01 

描述：角度编码器传感器  

#  1产品概述
1. 支持 TTL 串口 
2. 两种模式：串口模式、Modbus 模式。
3. 采用硅胶软质排线，专用接口易连接 。
4. 体积小、测量范围广、低功耗、寿命长、便于安装
5. 最高 100Hz 数据输出速率。输出速率 0.1～100Hz 可调节。
6. 模块内部自带电压稳定电路，工作电压 3.3-5V 连接方便。  

#  2性能参数
1. 电压：3.3-5V
2. 电流：<15mA 
3. 体积：：15mm*16mm*3mm*26 
4. 重量：8.55g
5. 轴心是3mm 外宽是15mm,B 是16mm，A是10mm, 2孔之间的是10.5mm
6. 数据接口：TTL 串口(波特率支持 4800-921600 可调节、9600(默认))
7. 角度量程：0～360° 
8. 角度精度：±0.1°
9. 分辨率：18BIT
10. 回传速率：0.1～100Hz 可调节

# 3.引脚说明
| 序号 | 名称 | 功能 |
| --- | --- | --- |
| 1 | VCC | 模块电源，3.3-5V输入 |
| 2 | RX | 串行数据输入 |
| 3 | TX | 串行数据输出 |
| 4 | NC | 保留 |
| 5 | NC | 保留 |
| 6 | GND | 地线 |


# <img src="https://cdn.nlark.com/yuque/0/2024/png/32619495/1709606314739-c27ddd41-82b0-48db-9e23-cef2a70c0cce.png" width="592.2461712249219" title="" crop="0,0,1,1" id="u093735c8" class="ne-image">
# 4.产品尺寸


公差0.05mm

<img src="https://cdn.nlark.com/yuque/0/2025/png/42356723/1745306758850-8c371752-305d-46b0-acd6-65a3c5a3c6d2.png" width="634.6666666666666" title="" crop="0,0,1,1" id="u2132c492" class="ne-image">

# 5.硬件连接方法
##  5.1 串口连接： 
1. 与电脑连接的时候需要先安装[**CH340串口驱动**](https://iot.wit-motion.cn/#/witmotion/literature/download?id=6ebf3d8c927f4b53aa25e7f065291bfa)**。**
2. 与开发评估板连接，如下图所示：  

编码器的VCC TX RX GND分别与评估板的+5V RX TX GND 对应相接。TYPE-C插到电脑上。

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650532962146-9b096041-0ff3-4a14-b4d0-2694313f43b0.png" width="553" title="" crop="0,0,1,1" id="u8536ffab" class="ne-image">

# 6.软件使用方法
##  6.1 连接方法 
1. 通过 USB 转串口模块连接上电脑，可以在设备管理器中查询到对应的端口号，如图所示 ：

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650533410925-215dd0ce-fbd2-42dc-a891-2bf4a0179a11.png" width="826" title="" crop="0,0,1,1" id="uf70cf6ee" class="ne-image">

1. 连接上位机

①自动搜索：

将传感器使用 USB 转 TTL 与电脑连接。打开上位机，模块类别选择JY-ME01，点击搜索设备，上位机会自动识别传感器模块。

<img src="https://cdn.nlark.com/yuque/0/2024/png/27793718/1729127330639-b1635815-a2cb-4a2f-b56a-989b728a88f7.png" width="1493.3333333333333" title="" crop="0,0,1,1" id="ub3d648d5" class="ne-image">

②手动添加：

型号类别选择JY-ME01，选择波特率（默认9600），手动点“+”号添加。

<img src="https://cdn.nlark.com/yuque/0/2024/png/27793718/1729127944955-b568abfe-b066-4333-ab35-eb59e8cbb89f.png" width="1493.3333333333333" title="" crop="0,0,1,1" id="u6363ad7f" class="ne-image">

##  6.2 模式切换 
传感器模块有 3 种工作模式：ASCII 模式，Modbus 模式，Modbus 主动输出模式。使用上位机时可直接点击“模式”进行选择，如需自行开发使用用户可根据下表进行操作与配置。 ASCII 模式切换为 Modbus 模式方法如下：  

| 模式 | ASCIIL | |
| --- | --- | --- |
| Modbus模式 | ASCIIL切换为Modbus模式<br/>1.从串口发送AT+MODE=1设置为Modbus模式<br/>注：如需多级联需要将传感器单独设置为同样波特率，不同ID。 | |
| | | |


 Modbus 模式切换为 ASCII 模式和切换成 Modbus 主动输出模式方法如下：  

| 模式 | Modbus模式切换 | |
| --- | --- | --- |
| ASCII模式 | 1.Modbus切换为ASCII模式<br/>2.使用AT指令设置回传速率<br/>例：设置1Hz回传，指令：AT+PRATE=1000 | |
| | | |
| Modbus主动输出模式 | Modbus模式切换为Modbus主动输出模式：<br/>1.从串口发送AT+MODE=1设置为Modbus模式<br/>2.使用AT+MRATE命令设置modbus回传速率<br/>例：设置1Hz回传，指令：AT+MRATE=1000 | |


 Modbus 主动输出模式切换成 Modbus 模式方法如下：  

| 模式 | Modbus主动输出模式切换 | |
| --- | --- | --- |
| Modbus | Modbus主动输出模式切换为Modbus模式<br/>1.从串口发送AT+MODE=1设置为Modbus模式<br/>2.使用AT+MRATE命令Modbus回传速率为0<br/>例：设置Modbus 回传速率为0指令：AT+MRATE=0 | |
| | | |


## 6.3ASCII 模式
= ASCII 模式，使用对应的 AT 指令与模块进行通信，使用简单快捷。使用 USB_TTL 将模块与电脑连接，使用提供上位机或串口助手发送AT 指令即可。 可通过串口助手发送指令。手动发送测试指令“AT”，回复“OK”即表示通信成功。如下图： 注：ASCII 模式只可以连接一个传感器模块。  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650533839843-5ecec5bc-bb89-4334-9138-e86b4071ace4.png" width="737" title="" crop="0,0,1,1" id="ufca0db04" class="ne-image">

 注：AT 指令只能连接一个传感器模块，AT 指令以换行符结束（如上图：勾选额外增加换行符）。收到“OK”为 ASCII 码格式（如上图：不勾选16进制显示）  

### 6.3.1 AT 指令集 
下面为 ASCII 模式下使用的 AT 指令表，用户可根据指令表进行自行开发。  

| 指令 | 功能 | 回复内容格式 |
| --- | --- | --- |
| AT | 检测连接是否正常 | OK |
| AT+VERSION=? | 查询当前版本号 | Version:<当前版本号> |
| AT+UART=1<br/>......<br/>AT+UART=9 | 更改波特率为4800-921600 | OK |
| AT+MODE=? | 查询当前模式 | +MODE |
| AT+MODE=0 | ASCII模式 | OK |
| AT+MODE=1 | Modbus | OK |
| AT+ID=? | 查询模块ID | +ID=＜ID＞ |
| AT+ID=＜0-254的数字＞ | 更高Modbus模式 | OK |
| AT+PRATE=0 | 设置为单次回传 | OK<br/>Yaw:＜z轴的角度＞ |
| AT+PRATE=＜10-10000＞ | 设置回传速度单位ms | OK<br/>Yaw:＜z轴的角度＞ |
| AT+MRATE=? | 查询当前Modbus速率 | +MRATE=＜MRATE＞ |
| AT+MRATE=0 | 设置为标准Modbus,一问一答 | OK |
| AT+MRATE=＜10-10000＞ | 当该寄存一旦北设置为非0状态，则进入主动输出的Modbus模式，即非标准Modus | OK<br/><br/> |
| AT+ZERO | 角度置零 | OK<br/> |


 注：所有的 AT 指令以回车换行符结束（必须勾选“额外增加换行符”）  

###  6.3.2“AT”指令 
“AT”指令为检测硬件连接是否正常。在发送栏输入“AT”（勾选“额外增加换行符”），点击发送，如回复“OK”即表示通信正常，否则表示通信异常。串口助手演示如下图：  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650534461425-ca1be7ef-25f4-4811-8478-77bd10b64adb.png" width="799" title="" crop="0,0,1,1" id="u131d19a7" class="ne-image">

### 6.3.3 “AT+VERSION=?”指令
**<font style="color:#DF2A3F;">注意：19704以下的版本不支持这个指令</font>**

Version:<当前版本号>，19704就是当前的版本号

<img src="https://cdn.nlark.com/yuque/0/2025/png/43192435/1738747469137-671816c3-0aca-454d-a107-2604151ce081.png" width="590" title="" crop="0,0,1,1" id="u8c219c6d" class="ne-image">

###  6.3.4“AT+UART”指令
“AT+UART”指令为更改串口波特率。检测通信正常之后，可以点击下方更改波特率按钮，也可手动发送指令“AT+UART=1”（波特率4800），“AT+UART=2”（波特率 9600），“AT+UART=3”（波特率19200），点击发送，如回复“OK”表示更改成功。 注意：更改波特率后需要手动更改上位机波特率，或点击自动搜索设备重新设置上位机波特率。 下图为更改波特率为 9600，需要手动设置波特率。串口助手演示  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650534508993-12bfbfd4-49b9-444d-9047-cefe9c76b0f2.png" width="752" title="" crop="0,0,1,1" id="u96686d69" class="ne-image">

###  6.3.5“AT+ID”指令 
“AT+ID”指令为更改查询模块 Modbus 地址。检测通信正常之后，点击“查询 ID”，或在发送栏输入“AT+ID=?”，点击发送。即可查询模块ID。例：回复“+ID=0”，表示当前模块地址为“0”。如发送“AT+ID=1”即可更改模块 ID 为 1，回复“OK”表示更改成功。地址可更改为0-254，即0x00-0xFE。具体操作如下图（默认地址为：0x00）：串口助手演示  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650534559777-0ff68acd-94dc-42ff-9ac8-6a27c493478e.png" width="745" title="" crop="0,0,1,1" id="u4fa76311" class="ne-image">

###  6.3.6“AT+PRATE”指令 
<font style="color:#DF2A3F;">注：修改回传速率前，先把波特率提高，再去改回传速率。</font>

“AT+PRATE”指令为更改模块回传速度。可手动发送相应指令设置“AT+PRATE=0”设置为单次回传，即发送一次回传一次。“AT+PRATE=1000”设置自定义的回传时间 1000，单位毫秒，即回传速率1Hz，可设置为10—10000（0.10 秒至 10 秒）。查询加速度前需要对模块进行初始化否决则将无法采集到正确的加速度数据（如设置为自动回传下次上电会自动初始化，并回传加速度数据）。具体操作如下图： 串口助手演示 

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650534853736-c1c7caeb-d096-411d-848e-b763500e3119.png" width="751" title="" crop="0,0,1,1" id="u0333f9e0" class="ne-image">

###  6.3.7“AT+MRATE”指令 
“AT+MRATE”指令为更改模块 modbus 模式下回传速度。可手动发送相应指令设置“AT+PRATE=0”设置为单次回传，即发送一次回传一次。“AT+MRATE=1000”设置自定义的回传时间 1000，单位毫秒，即回传速1Hz，可设置为 10～10000（0.10 秒至 10 秒）。查询加速度前需要对模块进行初始化否决则将无法采集到正确的加速度数据（如设置为自动回传下次上电会自动初始化，并回传加速度数据,注意此状态下为非标准modbus 通讯）  



###  6.3.8 "AT+ZERO"指令
角度置零。

###  6.3.9 上位机数据记录 
上位机在 ASCII 模式下有记录数据功能，可将传感器输出数据保存为TXT 文档，方便数据保存于数据分析。 数据保存使用方法，例如将传感器设置为 1Hz 自动回传，点击“开始记录”。  

<img src="https://cdn.nlark.com/yuque/0/2024/png/27793718/1729128426409-13a3cdd7-195f-4e67-877c-17f4f5bf40c0.png" width="1486.2222222222222" title="" crop="0,0,1,1" id="u9fb9eb15" class="ne-image">

 点击“结束记录”后弹出是否打开记录文件。如下图：  

<img src="https://cdn.nlark.com/yuque/0/2024/png/27793718/1729128483833-2a5298d4-1b9f-4f81-9310-e51a265ca9c4.png" width="1489.7777777777778" title="" crop="0,0,1,1" id="uebe112c6" class="ne-image">

 记录完成后可点击“结束记录”，弹窗提示是否打开记录文件。也可在上位机根目录下 DATA 文件夹中找到记录文件。记录文件如下图：  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650534967510-c4c20070-f353-42f4-ada0-1d3507846d87.png" width="886" title="" crop="0,0,1,1" id="u80d2fd18" class="ne-image">

##  6.4Modbus 模式 
### 6.41Modbus 模式说明
 Modbus 模式，使用 Modbus 协议采集数据使用 Modbus 模式的操作如下1 从串口发送指令 AT+MODE=1， 设置为 Modbus 模式 2 访问寄存器地址进行获取数据，寄存器地址表请参考5.4.3 小节

### 6.4.2Modbus 通信协议 
Modbus 通信，命令号分为两种读命令与写命令，0x03（读命令）读取相应寄存器数据，0x06（写命令）向相应寄存器写入数据。上位机发送数据帧  

| ID | 命令号 | 寄存器地址高位 | 寄存器地址低位 | 读取长度高位 | 读取长度低位 | CRC校验高位 | CRC校验低位 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ID | CMD | RegH | RegL | LenH | LenL | CRCH | CRCH |


 例：模块地址为 0x00，读命令 0x03，寄存器 0XD4（设备id），长度一位。指令：00 03 00 D4 00 01 C5 E3 

模块回复帧  

| ID | 命令号 | 数据长度 | 数据位1 | 数据位2 |  | CRC校验高位 | CRC校验低位 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ID | CMD | LenH | DataH | DataL | ...... | CRCH | CRCH |


 例：模块地址为 0x00，读命令 0x03，长度 2 位。回复如下指令：00 03 02 00 00 85 84 指令读取如下图：  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650535990683-f34ea6ec-d10c-4bbe-a216-6f350ab6353c.png" width="818" title="" crop="0,0,1,1" id="u64af9585" class="ne-image">

###  6.4.3Modbus 寄存器地址表 
| 寄存器名称 | 寄存器地址 | 访问操作 | 发送格式和示例（示例位访问地址：0×00的示例） |
| --- | --- | --- | --- |
| VERSION(版本号） |  0xD0   |  读/写   | 发送：00 03 00 D0 00 01 CRCH CRCL（单个读取）<br/>返回：00 03 02 34 C1 CRCH CRCL （0x34C1=13505）   |
| MODE（模式） |  0xD1 |  读/写   | 发送：00 06 00 D1 00 00 CRCH CRCL <br/>返回：00 06 00 D1 00 00 CRCH CRCL <br/>(更改回传模式为 asc)   |
| BAUD(波特率）<br/>取值：<br/>2：9600<br/>6：115200<br/>9：921600 |  0xD2 |  读/写   | 发送：00 03 00 D2 00 01 CRCH CRCL（读取波特率）<br/>发送： 00 06 00 D2 00 02 CRCH CRCL（2：9600默认）<br/>发送：00 06 00 D2 00 03 CRCH CRCL（6：115200）<br/>发送：00 06 00 D2 00 09 CRCH CRCL（9：921600）   |
| PRATE(回传速率)<br/>取值：<br/>1-10000：（单位ms/次）<br/>0：单次回传<br/><br/> |  0xD3 |  读/写   | 发送：00 03 00 D3 00 01 CRCH CRCL（读取回传速率）<br/>发送：00 06 00 D3 00 00 CRCH CRCL（0：单次）<br/>发送：00 06 00 D3 00 0A CRCH CRCL（10：100Hz）<br/>发送：00 06 00 D3 00 64 CRCH CRCL（100：10Hz）   |
| ID（设备 ID） 取值: 0-254   |  0xD4 |  读/写   | 发送：00 03 00 D4 00 01 CRCH CRCL（读取ID）<br/>发送：00 06 00 D4 00 50 CRCH CRCL（ID修改为0x50）   |
| ANGH（角度高 位寄存器）   |  0xD5 | 只读 | 发送：00 03 00 D5 00 01 CRCH CRCL（读取角度高位寄存器） <br/>接收：00 03 02 00 00 CRCH CRCL <br/>角度计算公式：[ANGH<<16|ANGL]/262144*360   |
| ANGL（角度低 位寄存器）   |  0xD6 | 只读 | 发送：00 03 00 D6 00 01 CRCH CRCL（读取角度低位寄存器） 接收：00 03 02 4E 48 CRCH CRCL <br/>角度计算公式：[ANGH<<16|ANGL]/262144*360   |
| MRATE（主动回 传间隔） <br/>取值：0~1000 0:不主动输出 其他:间隔时间 ms   |  0xD7 |  读/写   | 发送：00 06 00 D7 00 00 CRCH CRCL（0：标准Modbus）<br/>发送：00 06 00 D7 00 0A CRCH CRCL（10：间隔10ms）<br/>发送：00 06 00 D7 00 64 CRCH CRCL（100：间隔100ms）   |
| Modbus下角度置零   （需要版本号在<font style="color:#DF2A3F;">19704</font>及以上才可以使用） | 0xD8   0xD9 | 读/写 | 发送：00 06 00 d8 00 00 CRCH CRCL（将0xD8寄存器置零，延时100ms）<br/>接受：00 06 00 D8 00 00 08 20   发送：00 06 00 d9 00 00 CRCH CRCL（将0xD9寄存器置零,延时100ms）<br/>接受：00 06 00 D9 00 00 59 E0    发送：00 03 00 d5 00 02 CRCH CRCL(读取0xD5，0xD6寄存器的值）<br/>接受：00 03 04 <font style="color:#DF2A3F;">00 02 C7 57</font> 58 FD （读取角度值为250.08）   发送：00 06 00 d8 00 02 CRCH CRCL（将00 02写入0xD8寄存器，延时100ms）<br/>接受：00 06 00 D8 00 02 89 E1    发送：00 06 00 d9 C7 57 CRCH CRCL（将C7 57写入0xD9寄存器，延时100ms）   接受：00 06 00 D9 C7 57 4A 2E   发送：00 03 00 d5 00 02 CRCH CRCL(读取0xD5，0xD6寄存器的值）   接受：00 03 04 00 00 00 00 EA F3(返回的角度为0）       |


###  角度计算公式
发送指令读取角度及解析。

发→◇00 03 00 D5 00 02 D4 22 

收←◆00 03 04 00 02 91 BA A7 10 

公式：十进制数 / 262144 * 360 

<img src="https://cdn.nlark.com/yuque/0/2023/png/32619495/1690450324670-5be01742-584f-4085-ae96-9b740ed5f15a.png" width="318.2769324163857" title="" crop="0,0,1,1" id="uf55ff02a" class="ne-image"><img src="https://cdn.nlark.com/yuque/0/2023/png/32619495/1690450357419-1d6e0c3c-ec3e-4bfc-ac9d-ed0dd553e97d.png" width="318.2769324163857" title="" crop="0,0,1,1" id="uf8108712" class="ne-image">

<img src="https://cdn.nlark.com/yuque/0/2023/png/32619495/1690449938393-4bfa0835-3b1a-4eea-b52d-b7ffa097487e.png" width="802.7077158622071" title="" crop="0,0,1,1" id="ud679b6ac" class="ne-image">

<img src="https://cdn.nlark.com/yuque/0/2023/png/32619495/1690449951144-9b15b8c6-24de-4f6e-8c50-eb9af019db9f.png" width="1199.2615736524604" title="" crop="0,0,1,1" id="uf8e189a4" class="ne-image">

###  6.4.4 上位机 Modbus 连接 
连接电脑后，打开上位机，进入配置选择 Modbus 模式。选择波特率、端口号、ID 后添加设备，即可连接设备。  

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650536134194-f4740238-02ae-498c-b433-bc4ae0e4d089.png" width="800" title="" crop="0,0,1,1" id="ufcfa71b7" class="ne-image">

###  6.4.5 自动回传 Modbus 模式 
模块具有自动回传 Modbus 模式，自动回传 Modbus 模式下会主动回传航向角的数据，使用自动回传 Modbus 模式的方法 1 发送进入 Modbus 模式指令 AT+MODE=1 2 发送调整 Modbus 模式回传速率命令 AT+MRATE=数值  。

** 在该模式下回传的是 Modbus 指令，所以需要使用16 进制查看数据  **

**串口助手示例**

<img src="https://cdn.nlark.com/yuque/0/2022/png/26348092/1650536208896-7b931b81-8d5b-4bf5-ad36-e6b2f3051681.png" width="829" title="" crop="0,0,1,1" id="u618e8609" class="ne-image">

 例如：00 03 04 00 01 5F CF C2 97 

原始数据：00015FCF(16 进制) 90063(十进制)

角度数据：Angle = 90063 / 262144 * 360 = 123.682708  

# 7.联系我们
<img src="https://wit-motion.yuque.com/api/filetransfer/images?url=https%3A%2F%2Fwitpic-1253369323.cos.ap-guangzhou.myqcloud.com%2Fimg-md%2Fe6594cda72cedfeaefe9c62226410e68.jpeg&amp;sign=ea62784a9b2aef3825b070ab1669ddbcdaa63bdae4d665b13a1541b3b7103f0a" width="656" title="" crop="0,0,1,1" id="VFmZR" class="ne-image">

[深圳维特智能科技有限公司](http://www.wit-motion.cn/)

WitMotion ShenZhen Co., Ltd

电话: 0755-33185882

邮箱: [wit@wit-motion.com](mailto:wit@wit-motion.com)

网站： [http://www.wit-motion.cn](http://www.wit-motion.cn)

店铺: [https://robotcontrol.taobao.com](https://robotcontrol.taobao.com)

地址:<font style="color:rgb(24, 24, 24);">广东省-深圳市-光明区-西环大道143号光明云里智能园</font>
