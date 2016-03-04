# -*- coding: UTF-8 -*-
from datetime import datetime

from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from lxml import etree

import models as wx_models

@csrf_exempt
def token(request):
    if request.method == "GET":
        echostr = request.GET.get('echostr', '')
        return HttpResponse(echostr)
    else:
        xml_str = smart_str(request.body)
        xml = etree.fromstring(xml_str)
        from_user_name = xml.find("FromUserName").text
        result = deal_with_msg_type(xml)
        return HttpResponse(result)


def deal_with_msg_type(xml):
    result = ''
    msg_type = xml.find("MsgType").text
    create_time = xml.find('CreateTime').text
    create_time = datetime.fromtimestamp(float(create_time))
    return result