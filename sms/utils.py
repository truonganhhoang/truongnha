# -*- coding: utf-8 -*-
from models import sms, check_phone_number 
from datetime import date
import settings
import os
from django.core import mail

def to_ascii(string):
    result = ''
    uni_a = u'ăắẳẵặằâầấẩẫậàáảãạ'
    uni_A = u'ĂẮẲẴẶẰÂẦẤẨẪẬÀÁẢÃẠ'
    uni_o = u'óòỏõọơớờởỡợôốồỗộổ'
    uni_O = u'ÓÒỎÕỌƠỚỜỞỠỢÔỐỒỖỘỔ'
    uni_i = u'ìĩịỉí'
    uni_I = u'ÌĨỊỈÍ'
    uni_u = u'ủùũụúưừứựữử'
    uni_U = u'ỦÙŨỤÚƯỪỨỰỮỬ'
    uni_e = u'éèẽẻẹêếềễệể'
    uni_E = u'ÉÈẼẺẸÊẾỀỄỆỂ'
    uni_y = u'ýỳỷỹỵ'
    uni_Y = u'ÝỲỶỸỴ'
    uni_d = u'đ'
    uni_D = u'Đ'

    for c in string:
        for cc in ['a','o','i','u','e','d','y','A','O','I','U','E','D','Y']:
            exec("if c in uni_" + cc + ": c = " + "'" + cc + "'" )
        result += c
    return result

def _send_email(subject, message, from_addr=None, to_addr=[]):
    mail.send_mail(settings.EMAIL_SUBJECT_PREFIX + subject,
            message,
            settings.EMAIL_HOST_USER,
            to_addr)

# school parameter here is for hitting db avoidance purpose
def _send_sms(phone, content, user, receiver=None, save_to_db=True,
        school=None, is_task_called=False):
    phone = check_phone_number(phone)
    try:
        if not school:
            school = user.userprofile.organization
    except Exception:
        pass
    if phone:
        if school:
            if school.id in [42, 44]: raise Exception('NotAllowedSMS')
            content = to_ascii(u'Truong %s thong bao:\n%s' % (
                school, content))
        else:
            content = to_ascii(u'Truongnha.com thong bao:\n%s' % content)
        existing = sms.objects.filter(phone=phone, content=content).count()
        sending = sms.objects.filter(phone=phone, content=content,
                recent=True).count()
        if sending: return None
        if existing > 0:
            failed = sms.objects.filter(phone=phone, content=content, 
                    success=False).count()
            if failed: s = sms.objects.filter(phone=phone, content=content,
                    success=False)[0]
            else: s = None
        else:
            s = sms.objects.create(phone=phone, content=content, sender=user,
                receiver=receiver, recent=True, success=False)
        if s:
            if not settings.DEBUG and not is_task_called:
                return s.send_sms.delay(s, school=school)
            else:
                return s._send_sms(school=school)
        else:
            return None

def send_SMS_then_email(phone, content, user, receiver=None, save_to_db=True,
        school=None, is_task_called=False, subject=None, message=None,
        from_addr=None, to_addr=[]):
    phone = check_phone_number(phone)
    try:
        if not school:
            school = user.userprofile.organization
    except Exception:
        pass
    if phone:
        if school:
            if school.id in [42, 44]: raise Exception('NotAllowedSMS')
            content = to_ascii(u'Truong %s thong bao:\n%s' % (
                school, content))
        else:
            content = to_ascii(u'Truongnha.com thong bao:\n%s' % content)
        existing = sms.objects.filter(phone=phone, content=content).count()
        sending = sms.objects.filter(phone=phone, content=content,
                recent=True).count()
        # the sms is being sent, ignore it
        if sending: return None
        if existing > 0:
            failed = sms.objects.filter(phone=phone, content=content, 
                    success=False).count()
            if failed: s = sms.objects.filter(phone=phone, content=content,
                    success=False)[0]
            else: s = None
        else:
            s = sms.objects.create(phone=phone, content=content, sender=user,
                receiver=receiver, recent=True, success=False)
        # if s is a new message, send it
        if s:
            if not settings.DEBUG:
                return s.send_sms_then_email.delay(s, school=school,
                        subject=subject, message=message,
                        from_addr=from_addr, to_addr=to_addr)
            else:
                return s._send_sms(school=school)
        else: # s is already sent
            return None

def send_email(subject, message, from_addr=None, to_addr=[]):
    #msg = MIMEText(message.encode('utf-8'), _charset='utf-8')
    #server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
    #server.ehlo()
    #server.starttls()
    #server.ehlo()
    #server.login(GMAIL_LOGIN,GMAIL_PASSWORD)
    #for to_address in to_addr:
    #    msg['Subject'] = subject
    #    msg['From'] = from_addr
    #    msg['To'] = to_address
    #    server.sendmail(from_addr, to_address, msg.as_string())
    #server.close()
    if not settings.DEBUG:
        return task_send_email.delay(subject, message, from_addr, to_addr)
    else:
        _send_email(subject, message, from_addr, to_addr)

def sendSMS(phone, content, user, receiver=None, save_to_db=True, school=None):
    if not settings.DEBUG:
        task = _send_sms(phone, content, user, receiver, save_to_db, school)
        if task: return '1'
        else: return None
    else:
        return _send_sms(phone, content, user, receiver, save_to_db, school)

def send_sms_summary_mark(student, content, marks, dds, hk, user,
        cl=None, school=None):
    phone = check_phone_number(student.sms_phone)
    try:
        if not school:
            school = user.userprofile.organization
    except Exception:
        pass
    if phone:
        if school:
            if school.id in [42, 44]: raise Exception('NotAllowedSMS')
            if cl:
                sms_cont = to_ascii(
                        u'Truong %s thong bao:\nEm %s lop %s co %s\nTinh den ngay %s'\
                                % (unicode(school), student.short_name(),
                                    cl, content,
                                    unicode(date.today().strftime('%d\%m'))))
            else:
                sms_cont = to_ascii(
                        u'Truong %s thong bao:\nEm %s co %s\nTinh den ngay %s'\
                                % (unicode(school), student.short_name(),
                                    content,
                                    unicode(date.today().strftime('%d\%m'))))
        else:
            raise Exception('SchoolIsNone')

        s = sms.objects.filter(phone=phone, content=sms_cont, type='THONG_BAO')
        if len(s) > 0:
            s = s[0]
            s.recent = True
            s.success = False
            s.save()
        else:
            s = sms(phone=phone, content=sms_cont,
                    type='THONG_BAO', receiver=student.user_id,
                    sender=user, recent=True, success=False)
            s.save()
        if not settings.DEBUG:
            return s.send_mark_sms.delay(s, marks=marks, dds=dds, hk=hk, school=school)
        else:
            return s._send_mark_sms(marks, dds, hk, school=school)
    else:
        raise Exception('InvalidPhoneNumber')

from celery import task

@task()
def task_send_email(subject, message, from_addr=None, to_addr=[]):
    mail.send_mail(settings.EMAIL_SUBJECT_PREFIX + subject,
                message,
                settings.EMAIL_HOST_USER,
                to_addr)

def save_file(file):
    saved_file = open(os.path.join(settings.TEMP_FILE_LOCATION,
        'sms_input.xls'),
        'wb+')
    for chunk in file.chunks():
        saved_file.write(chunk)
    saved_file.close()
    return 'sms_input.xls'
