# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.template.loader import render_to_string
from .models import SelectScript
from blueking.component.shortcuts import get_client_by_user
from blueking.component.shortcuts import get_client_by_request
import logging, base64, copy
from django.http.response import JsonResponse


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
        info = {}
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
        hosts = []
    return hosts


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
    return render(request, 'home_application/record.html')


