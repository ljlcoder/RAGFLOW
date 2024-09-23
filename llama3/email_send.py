import requests

domain_name = "sandbox000e649976434b279945a954878ef16a.mailgun.org"
url = "https://api.mailgun.net/v3/" + domain_name + "/messages"

data = {
        "from": "mailgun@sandbox000e649976434b279945a954878ef16a.mailgun.org", #set your from mail address here
        "to": "xxx@qq.com",
        "subject": '测试邮件',
        "text": '试一下能发过去吗',
    }


#headers = {"Content-Type": "multipart/form-data"}   headers=headers,

response = requests.post(url,  auth=('api','45a854925b30fcf651de73bd15512ca1-2175ccc2-f4f07960'),data=data,)

data = response.json()
print(data)


