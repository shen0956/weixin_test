# -*- coding: UTF-8 -*-
import time
import json
from datetime import datetime, timedelta
import ConfigParser

import requests
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from lxml import etree

from weixin_crypt.WXBizMsgCrypt import WXBizMsgCrypt
import models as wx_models


cf = ConfigParser.ConfigParser()
cf.read('./qy/qy.conf')
WEIXIN_TOKEN = cf.get('weixin', 'token')
WEIXIN_ENCODINGAESKEY = cf.get('weixin', 'encodingaeskey')
WEIXIN_CORPID = cf.get('weixin', 'corpid')
SECRET = cf.get('weixin', 'secret')
print WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID, SECRET


@csrf_exempt
def token(request):
    msg_signature = request.GET.get('msg_signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')
    print msg_signature, timestamp, nonce, echostr
    wxcpt = WXBizMsgCrypt(WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID)
    if request.method == "GET":
        ret, echostr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
        return HttpResponse(echostr)
    else:
        result = ''
        xml_str = smart_str(request.body)
        ret, msg = wxcpt.DecryptMsg(xml_str, msg_signature, timestamp, nonce)
        if ret == 0:
            xml = etree.fromstring(msg)
            to_user_name = xml.find("ToUserName").text
            print u'------ 企业号CorpID: %s ------'.encode('gbk') % to_user_name
            from_user_name = xml.find("FromUserName").text
            print u'------ 成员UserID: %s ------'.encode('gbk') % from_user_name
            msg_type = xml.find("MsgType").text
            print u'------ 消息类型: %s ------'.encode('gbk') % msg_type
            create_time = xml.find('CreateTime').text
            create_time = datetime.fromtimestamp(float(create_time))
            if msg_type == 'event':
                event = xml.find('Event').text
                print u'------ 事件类型: %s ------'.encode('gbk') % event
                if event == 'click':
                    event_key = xml.find('EventKey').text
                    print u'------ 事件KEY值: %s ------'.encode('gbk') % event_key
                    if event_key == 'DERHINO_001':
                        weixin_user = get_user(from_user_name)
                        weixin_event = wx_models.WeixinEvent()
                        weixin_event.weixin_user = weixin_user
                        weixin_event.event_key = 'DERHINO_001'
                        weixin_event.created = create_time
                        weixin_event.save()
                        weixin_position = wx_models.WeixinPosition()
                        weixin_position.weixin_event = weixin_event
                        weixin_position.save()
                        text_msg_reply_xml(from_user_name, nonce, timestamp, 'aaaa')
        return HttpResponse(result)


# 获取成员
def get_user(user_id):
    access_token = get_access_token()
    try:
        weixin_user = wx_models.WeixinUser.objects.get(userid=user_id)
    except wx_models.WeixinUser.DoesNotExist:
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token=%s&userid=%s' % (access_token, user_id)
        req = requests.get(url)
        res = json.loads(req.content)
        weixin_user = wx_models.WeixinUser()
        weixin_user.userid = res['userid']
        weixin_user.name = res['name']
        weixin_user.gender = res['gender']
        weixin_user.email = res.get('email')
        weixin_user.mobile = res.get('mobile')
        weixin_user.save()
        return weixin_user
    else:
        return weixin_user

# 获取AccessToken
def get_access_token():
    try:
        weixin_token = wx_models.WeixinToken.objects.latest()
    except wx_models.WeixinToken.DoesNotExist:
        refresh_token = 1
    else:
        if timezone.now() >= weixin_token.created + timedelta(seconds=7200):
            refresh_token = 1
        else:
            return weixin_token.access_token
    if refresh_token == 1:
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' %(WEIXIN_CORPID, SECRET)
        req = requests.get(url)
        res = json.loads(req.content)
        weixin_token = wx_models.WeixinToken()
        weixin_token.access_token = res['access_token']
        weixin_token.save()
        return weixin_token.access_token


def text_msg_reply_xml(to_user_name, nonce, timestamp, message):
    #根据传进来的参数  回复http响应  回复text消息
    xml = '''
        <xml>
        <ToUserName><![CDATA[%s]]></ToUserName>
        <FromUserName><![CDATA[%s]]></FromUserName>
        <CreateTime>%s</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[%s]]></Content>
        </xml>''' % (to_user_name, WEIXIN_CORPID, str(int(time.time())), message)
    wxcpt = WXBizMsgCrypt(WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID)
    ret, result = wxcpt.EncryptMsg(xml, nonce, timestamp)
    if ret == 0:
        return result
    else:
        print 'error'
