import requests

domain_name = "xxx.mailgun.org"
url = "https://api.mailgun.net/v3/" + domain_name + "/messages"

data = {
        "from": "mailgun@xxx.mailgun.org", #set your from mail address here
        "to": "xxx@qq.com",
        "subject": '测试邮件',
        "text": '试一下能发过去吗',
    }


#headers = {"Content-Type": "multipart/form-data"}   headers=headers,

response = requests.post(url,  auth=('api','xxx-xxx-xxx'),data=data,)

data = response.json()
print(data)


