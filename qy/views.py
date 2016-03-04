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
    msg_signature = request.GET.get('msg_signature', '')
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    echostr = request.GET.get('echostr', '')
    wxcpt = WXBizMsgCrypt(WEIXIN_TOKEN, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID)
    if request.method == "GET":
        ret, echostr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
        return HttpResponse(echostr)
    else:
        xml_str = smart_str(request.body)
        ret, xml_str = wxcpt.DecryptMsg(xml_str, msg_signature, timestamp, nonce)
        if ret == 0:
            xml = etree.fromstring(xml_str)
            result = ''
        # msg_type = xml.find("MsgType").text
        # create_time = xml.find('CreateTime').text
        # create_time = datetime.fromtimestamp(float(create_time))
        # result = ''
        # event = xml.find('Event').text
        # print event
        # if event == 'click':
        #     event_key = xml.find('EventKey').text
        #     if event_key == 'DERHINO_001':
        #         message = '请输入机器编号（例如：R001,M008...）：'
        #         xml = '''
        #             <xml>
        #             <ToUserName><![CDATA[%s]]></ToUserName>
        #             <FromUserName><![CDATA[%s]]></FromUserName>
        #             <CreateTime>%s</CreateTime>
        #             <MsgType><![CDATA[text]]></MsgType>
        #             <Content><![CDATA[%s]]></Content>
        #             </xml>''' % (from_user_name, WEIXIN_CORPID, str(int(time.time())), message)
        #         wxcpt=WXBizMsgCrypt(WEIXIN_Token, WEIXIN_ENCODINGAESKEY, WEIXIN_CORPID)
        #         ret, sEncryptMsg = wxcpt.EncryptMsg(xml, nonce, timestamp)
        #         print ret
        #         print sEncryptMsg
        return HttpResponse(result)


