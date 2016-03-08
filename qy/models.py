# -*- coding: UTF-8 -*-
from django.db import models


class WeixinToken(models.Model):
    access_token = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weixin_token'
        get_latest_by = 'created'


class WeixinUser(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.CharField(max_length=20)
    openid = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=20)
    gender = models.SmallIntegerField()
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'weixin_user'


class WeixinEvent(models.Model):
    id = models.AutoField(primary_key=True)
    weixin_user = models.ForeignKey(WeixinUser)
    event_key = models.CharField(max_length=20)
    created = models.DateTimeField()

    class Meta:
        db_table = 'weixin_event'
        get_latest_by = 'created'


class WeixinPosition(models.Model):
    id = models.AutoField(primary_key=True)
    device_num = models.CharField(max_length=10, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    lat = models.FloatField(u'纬度', null=True, blank=True)
    lng = models.FloatField(u'经度', null=True, blank=True)
    weixin_event = models.OneToOneField(WeixinEvent, db_column='WEIXIN_EVENT')
    msg_id01 = models.BigIntegerField(u'消息id', null=True, blank=True)
    time01 = models.DateTimeField(u'消息创建时间', null=True, blank=True)
    msg_id02 = models.BigIntegerField(u'消息id', db_column='MSG_ID02', null=True, blank=True)
    time02 = models.DateTimeField(u'消息创建时间', db_column='TIME02', null=True, blank=True)
    msg_id03 = models.BigIntegerField(u'消息id', db_column='MSG_ID03', null=True, blank=True)
    scale03 = models.IntegerField(u'地图缩放大小', db_column='SCALE03', null=True, blank=True)
    label03 = models.CharField(u'地理位置信息', max_length=100, db_column='LABEL03', null=True, blank=True)
    time03 = models.DateTimeField(u'消息创建时间', db_column='TIME03', null=True, blank=True)
    msg_id04 = models.BigIntegerField(u'消息id', db_column='MSG_ID04', null=True, blank=True)
    pic04 = models.ImageField(upload_to='position_img', null=True, blank=True)
    pic_url04 = models.URLField(u'图片链接', db_column='PIC_URL04', null=True, blank=True)
    media_id04 = models.CharField(u'图片消息媒体id，可以调用多媒体文件下载接口拉取数据。', max_length=100, db_column='MEDIA_ID04', null=True, blank=True)
    time04 = models.DateTimeField(u'消息创建时间', db_column='TIME04', null=True, blank=True)
    msg_id05 = models.BigIntegerField(u'消息id', db_column='MSG_ID05', null=True, blank=True)
    content05 = models.CharField(u'屏幕朝向', max_length=20, db_column='CONTENT05', null=True, blank=True)
    time05 = models.DateTimeField(u'消息创建时间', db_column='TIME05', null=True, blank=True)
    # audit_status = models.SmallIntegerField(u'审核状态', db_column='AUDIT_STATUS', default=0)
    # audit_user = models.ForeignKey(User, db_column='AUDIT_USER', null=True, blank=True)
    # audit_date = models.DateTimeField(u'审核日期', db_column='AUDIT_DATE', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        db_table = 'weixin_position'
        get_latest_by = 'created'