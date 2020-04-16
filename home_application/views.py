# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.template.loader import render_to_string
from .models import SelectScript, Doinfo
from blueking.component.shortcuts import get_client_by_user
from blueking.component.shortcuts import get_client_by_request
import logging, base64, copy, datetime
from datetime import datetime
from django.http.response import JsonResponse
from .celery_tasks import async_status

client = get_client_by_user("2496234829")
logger = logging.getLogger(__name__)


# 查询业务
def get_biz_info():
    kwargs = {"fields": ["bk_biz_id", "bk_biz_name"]}
    res = client.cc.search_business(kwargs)
    biz_name = []
    biz_id = []
    info = {}
    if res.get('result', False):
        for i in res['data']['info']:
            biz_name.append(i['bk_biz_name'])
            biz_id.append(i['bk_biz_id'])
            info = dict(zip(biz_name, biz_id))
    else:
        logger.error(u'请求业务列表失败：%s' % res.get('message'))
    return info


# 根据条件查询主机
def ser_host(biz_id):
    kwargs = {"bk_biz_id": biz_id}
    res = client.cc.search_host(kwargs)
    hosts = []
    if res.get('result', False):
        for host_info in res['data']['info']:
            hosts.append({
                "ip": host_info['host']['bk_host_innerip'],
                "os": host_info['host']["bk_os_name"],
                "host_id": host_info['host']["bk_host_id"],
                "name": host_info['host']['bk_host_name'],
                "cloud_id": host_info['host']["bk_cloud_id"][0]["id"]
            })
    else:
        logger.error(u'查询主机列表失败：%s' % res.get('message'))
    return hosts


# 查询所有用户信息
def get_usernames():
    res = client.bk_login.get_all_users()
    usernames = []
    if res.get('result', False):
        for i in res['data']:
            usernames.append(i['bk_username'])
    else:
        logger.error(u'查询所有用户列表失败：%s' % res.get('message'))
    return usernames


# ajax 请求业务相应的host,并返回
def get_host(request):
    biz_id = request.GET.get('biz_id')
    if biz_id:
        biz_id = int(biz_id)
    else:
        return JsonResponse({'result': False, 'message': "must provide biz_id to get hosts"})
    data = ser_host(biz_id)
    table_data = render_to_string('home_application/execute_tbody.html', {'data': data})
    return JsonResponse({"result": True, "message": "success", "data": table_data})


# 执行任务
def execute_script(request):
    biz_id = request.POST.get('biz_id')
    script_id = request.POST.get('script_id')
    obj = SelectScript.objects.get(id=script_id)
    objtest = base64.b64encode(obj.scriptcontent.encode('utf-8'))
    ip_id = request.POST.getlist('ip_id[]')
    ips = {"bk_cloud_id": 0, "ip": 0}
    ip_info = []
    for i in ip_id:
        ips['ip'] = i
        ip_info.append(copy.deepcopy(ips))
    kwargs = {"bk_biz_id": biz_id,
              "script_content": str(objtest, 'utf-8'),
              "account": "root",
              "script_type": 1,
              "ip_list": ip_info}
    execute_data = client.job.fast_execute_script(kwargs)
    if execute_data.get('result', False):
        data = execute_data['data']
        result = True
        message = str(execute_data.get('message'))

        async_status.apply_async(args=[client, data, biz_id, obj, ip_id], kwargs={})

    else:
        data = []
        result = False
        message = "False"
        logger.error(u'查询主机列表失败：%s' % execute_data.get('message'))
    return JsonResponse({"result": result, "message": message, "data": data})


def tasks(request):
    tasks = SelectScript.objects.all()
    data = {"tasks": tasks,
            "info": get_biz_info().items(),
            "data": ser_host(2)}
    return render(request, 'home_application/tasks.html', data)


def record(request):
    tasks = SelectScript.objects.all()
    doinfos = Doinfo.objects.all()
    data = {"info": get_biz_info().items(),
            "usernames": get_usernames(),
            "tasks": tasks,
            "doinfos": doinfos}
    return render(request, 'home_application/record.html', data)


# 根据前端返回的数据进行查询
def inquiry(request):
    try:
        biz_id = request.POST.get('biz_id')
        username = request.POST.get('username')
        script_id = request.POST.get('script_id')
        time = request.POST.get('time')  #"2020/03/27 - 2020/03/27"
        doinfo = Doinfo.objects.all()
        doinfo = doinfo.filter(businessname=int(biz_id)).filter(username=username).filter(script_id=int(script_id))
        starttime, endtime = time.split('-')
        starttime = starttime.strip().replace('/', '-') + ' 00:00:00'
        endtime = endtime.strip().replace('/', '-') + ' 23:59:00'
        start_time = datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(endtime, '%Y-%m-%d %H:%M:%S')
        doinfo = doinfo.filter(starttime__range=(start_time, end_time))
        data = [info.to_dict() for info in doinfo]
        # print(data)
        table_data = render_to_string('home_application/record_tbody.html', {'doinfos': data})
        result = True
        message = "success"
    except Exception as err:
        table_data = []
        result = False
        message = str(err)
    return JsonResponse({"result": result, "message": message, "data": table_data})
