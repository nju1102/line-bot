from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
#import openai
import time
import traceback
#======python的函數庫==========

from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('4RQJzYTr/liAbmy5txUaqSEOrN/CJwbrlHCPwYevdDxmdIxUsmFryCI8V4UprQ2xLp12flIe3tTnJmY1q/fCGSg6rSKRG73hrTq4Uoqv6/6kHpVx dB04t89/1O/w1cDnyilFU='))
# Channel Secret
handler = WebhookHandler(os.getenv('8eb33bfd76d9fe0db1091bb61cac7eea'))
# OPENAI API Key初始化設定
#openai.api_key = os.getenv('OPENAI_API_KEY')

endpoint = os.getenv('END_POINT')
credential = AzureKeyCredential(os.getenv('AZURE_KEY'))
knowledge_base_project = os.getenv('PROJECT')
deployment = 'production'

#def GPT_response(text):
    # 接收回應
    #response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    #print(response)
    # 重組回應
    #answer = response['choices'][0]['text'].replace('。','')
    #return answer

def QA_response(text):
    client = QuestionAnsweringClient(endpoint, credential)
    with client:
        question=text
        output = client.get_answers(
            question = question,
            project_name=knowledge_base_project,
            deployment_name=deployment
        )
    return output.answers[0].answer

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg[0]=='-':
        try:
            QA_answer = QA_response(msg)
            print(QA_answer)
            if QA_answer!='No good match found in KB':
                line_bot_api.reply_message(event.reply_token, TextSendMessage(QA_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('QA Error'))
         

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
