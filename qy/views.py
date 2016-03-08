# -*- coding: UTF-8 -*-
import time
from datetime import datetime, timedelta
import ConfigParser

import requests
from django.core.files.base import ContentFile
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
            weixin_user = get_user(from_user_name)
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
                        weixin_event = wx_models.WeixinEvent()
                        weixin_event.weixin_user = weixin_user
                        weixin_event.event_key = 'DERHINO_001'
                        weixin_event.created = create_time
                        weixin_event.save()
                        weixin_position = wx_models.WeixinPosition()
                        weixin_position.weixin_event = weixin_event
                        weixin_position.save()
                        result = weixin_position_reply(weixin_position, weixin_user, nonce, timestamp)
            elif msg_type == 'text':
                result = deal_wih_text(xml, weixin_user, nonce, timestamp)
            elif msg_type == 'location':
                result = deal_with_location(xml, weixin_user, nonce, timestamp)
            elif msg_type == 'image':
                result = deal_with_image(xml, weixin_user, nonce, timestamp)
        return HttpResponse(result)


# 获取成员
def get_user(user_id):
    access_token = get_access_token()
    try:
        weixin_user = wx_models.WeixinUser.objects.get(userid=user_id)
    except wx_models.WeixinUser.DoesNotExist:
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token=%s&userid=%s' % (access_token, user_id)
        req = requests.get(url)
        res = req.json()
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
        if datetime.now() >= weixin_token.created + timedelta(seconds=7200):
            refresh_token = 1
        else:
            return weixin_token.access_token
    if refresh_token == 1:
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s' %(WEIXIN_CORPID, SECRET)
        req = requests.get(url)
        res = req.json()
        weixin_token = wx_models.WeixinToken()
        weixin_token.access_token = res['access_token']
        weixin_token.save()
        return weixin_token.access_token


# 接收图片消息
def deal_with_image(xml, weixin_user, nonce, timestamp):
    result = ''
    pic_url = xml.find('PicUrl').text
    media_id = xml.find('MediaId').text
    msg_id = xml.find('MsgId').text
    create_time = xml.find('CreateTime').text
    create_time = datetime.fromtimestamp(float(create_time))
    try:
        user_event = weixin_user.weixinevent_set.filter(created__gte=datetime.now()-timedelta(minutes=15)).latest()
    except wx_models.WeixinEvent.DoesNotExist:
        result = text_msg_reply_xml(weixin_user.userid, '事件不存在', nonce, timestamp)
    else:
        if user_event.event_key == 'DERHINO_001':
            weixin_position = user_event.weixinposition
            if weixin_position.msg_id01 and weixin_position.msg_id02 and weixin_position.msg_id03 \
                    and not weixin_position.msg_id04:
                pic_name = '%s_%s.jpg'%(weixin_position.device_num, datetime.now().strftime('%Y%m%d%H%M%S'))
                weixin_position.msg_id04 = msg_id
                weixin_position.pic_url04 = pic_url
                weixin_position.media_id04 = media_id
                weixin_position.time04 = create_time
                weixin_position.pic04.save(pic_name, ContentFile(get_media(media_id)))
                weixin_position.save()
            result = weixin_position_reply(weixin_position, weixin_user, nonce, timestamp)
    return result


# 处理文本消息
def deal_wih_text(xml, weixin_user, nonce, timestamp):
    content = xml.find('Content').text.strip()
    msg_id = xml.find('MsgId').text
    create_time = xml.find('CreateTime').text
    create_time = datetime.fromtimestamp(float(create_time))
    result = ''
    # 处理事件之后的文本消息
    try:
        user_event = weixin_user.weixinevent_set.filter(created__gte=datetime.now()-timedelta(minutes=15)).latest()
    except wx_models.WeixinEvent.DoesNotExist:
        result = text_msg_reply_xml(weixin_user.userid, '事件不存在', nonce, timestamp)
    else:
        if user_event.event_key == 'DERHINO_001':
            weixin_position = user_event.weixinposition
            # 记录机器编号
            if not weixin_position.msg_id01:
                weixin_position.device_num = content
                weixin_position.time01 = create_time
                weixin_position.msg_id01 = msg_id
                weixin_position.save()
            # 记录小区名
            elif weixin_position.msg_id01 and not weixin_position.msg_id02:
                weixin_position.position = content
                weixin_position.msg_id02 = msg_id
                weixin_position.time02 = create_time
                weixin_position.save()
            # 记录屏幕朝向
            elif weixin_position.msg_id01 and weixin_position.msg_id02 and weixin_position.msg_id03 and \
                    weixin_position.msg_id04 and not weixin_position.msg_id05:
                weixin_position.content05 = content
                weixin_position.msg_id05 = msg_id
                weixin_position.time05 = create_time
                weixin_position.save()
            result = weixin_position_reply(weixin_position, weixin_user, nonce, timestamp)
    return result


# 处理地理位置消息
def deal_with_location(xml, weixin_user, nonce, timestamp):
    result = ''
    location_x = xml.find('Location_X').text
    location_y = xml.find('Location_Y').text
    scale = xml.find('Scale').text
    label = xml.find('Label').text
    msg_id = xml.find('MsgId').text
    create_time = xml.find('CreateTime').text
    create_time = datetime.fromtimestamp(float(create_time))
    # 通过baidu坐标转换API转换成百度地图中使用的坐标
    data = {
        'coords': location_y + ',' + location_x,
        'from': 3,
        'to': 5,
        'ak': '42fb3f560f5353afa32644f635d48ccc',
    }
    url = 'http://api.map.baidu.com/geoconv/v1/'
    req = requests.get(url, params=data)
    res = req.json()
    longitude = res['result'][0]['x']
    latitude = res['result'][0]['y']
    try:
        user_event = weixin_user.weixinevent_set.filter(created__gte=datetime.now()-timedelta(minutes=15)).latest()
    except wx_models.WeixinEvent.DoesNotExist:
        result = text_msg_reply_xml(weixin_user.openid, u'事件不存在')
    else:
        if user_event.event_key == 'DERHINO_001':
            weixin_position = user_event.weixinposition
            if weixin_position.msg_id01 and weixin_position.msg_id02 and not weixin_position.msg_id03:
                weixin_position.msg_id03 = msg_id
                weixin_position.lat = latitude
                weixin_position.lng = longitude
                weixin_position.time03 = create_time
                weixin_position.scale03 = scale
                weixin_position.label03 = label
                weixin_position.save()
            result = weixin_position_reply(weixin_position, weixin_user, nonce, timestamp)
    return result


# 点位标记响应
def weixin_position_reply(weixin_position, weixin_user, nonce, timestamp):
    if not weixin_position.msg_id01:
        message = '请输入机器编号（例如：R001,M008...）：'
    elif weixin_position.msg_id01 and not weixin_position.msg_id02:
        message = '请输入小区名（例如：阳光城市花园一期...）：'
    elif weixin_position.msg_id01 and weixin_position.msg_id02 and not weixin_position.msg_id03:
        message = '请发送机器位置信息（使用微信发送位置功能，发送尽可能准确的位置）：'
    elif weixin_position.msg_id01 and weixin_position.msg_id02 and weixin_position.msg_id03 and \
            not weixin_position.msg_id04:
        message = '请发送机器图片：'
    elif weixin_position.msg_id01 and weixin_position.msg_id02 and weixin_position.msg_id03 and \
            weixin_position.msg_id04 and not weixin_position.msg_id05:
        message = '请发送机器朝向信息：'
    elif weixin_position.msg_id01 and weixin_position.msg_id02 and weixin_position.msg_id03 and \
            weixin_position.msg_id04 and weixin_position.msg_id05:
        message = '恭喜你完成全部操作，可以前往下个目的地了，一路顺风=。='
    else:
        message = '无效输入，你想干什么？'
    result = text_msg_reply_xml(weixin_user.userid, nonce, timestamp, message)
    return result


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
    xml = xml.encode('utf8')
    ret, result = wxcpt.EncryptMsg(xml, nonce, timestamp)
    if ret == 0:
        return result
    else:
        print 'error'


def get_media(media_id):
    access_token = get_access_token()
    url = 'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s'%(access_token, media_id)
    return requests.get(url).content