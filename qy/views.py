# -*- coding: UTF-8 -*-
import time
from datetime import datetime
import ConfigParser

from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from lxml import etree

from weixin_crypt.WXBizMsgCrypt import WXBizMsgCrypt

@csrf_exempt
def token(request):
    cf = ConfigParser.ConfigParser()
    cf.read('./qy/qy.conf')
    WEIXIN_TOKEN = cf.get('weixin', 'token')
    WEIXIN_ENCODINGAESKEY = cf.get('weixin', 'encodingaeskey')
    WEIXIN_CORPID = cf.get('weixin', 'corpid')
    print WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID
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
            if msg_type == 'event':
                event = xml.find('Event').text
                print u'------ 事件类型: %s ------'.encode('gbk') % event
                if event == 'click':
                    event_key = xml.find('EventKey').text
                    print u'------ 事件KEY值: %s ------'.encode('gbk') % event_key
                    if event_key == 'DERHINO_001':
                        xml = '''
                            <xml>
                            <ToUserName><![CDATA[%s]]></ToUserName>
                            <FromUserName><![CDATA[%s]]></FromUserName>
                            <CreateTime>%s</CreateTime>
                            <MsgType><![CDATA[text]]></MsgType>
                            <Content><![CDATA[%s]]></Content>
                            </xml>''' % (from_user_name, WEIXIN_CORPID, str(int(time.time())), 'aaaa')
                        wxcpt=WXBizMsgCrypt(WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID)
                        ret, result = wxcpt.EncryptMsg(xml, nonce, timestamp)
                        print ret
        return HttpResponse(result)


