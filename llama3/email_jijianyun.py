import requests
import json




url = "https://chat.jijyun.cn/v1/openapi/exposed/101544_1524_jjyibotID_afb0ac23709645cbae2edc7d293b4165/execute/?apiKey=McqK2D0aWAeuvzTxxt1765xn1705900572"

payload = json.dumps({
    "instructions": '随便写点东西发送到xxx@163.com',
    "preview_only": False
})
headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Host': 'chat.jijyun.cn',
    'Connection': 'keep-alive',
    'Cookie': 'acw_tc=xxxxxxxxxxxxxxx'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)