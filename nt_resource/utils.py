from uuid import uuid4
from nt_resource.models import CatNormalResource
from web.celery import app as celery_app
from nt_core.exceptions import RsError
from nt_app.cache import get_cache_cat_data


def add_normal_cat_data(data):
    """
    构建数据model  用yield每次返回1000条数据
    :param data
    :return:
    """
    tmp_cat_normal_models = []

    for cat_data in data:
        response_time = cat_data.get('response_time')
        request_count = cat_data.get('request_count') or 1
        fail_count = cat_data.get('fail_count') or 1
        cat_data['id'] = str(uuid4())
        if response_time < 1.2 and (fail_count / request_count) < 0.2:
            cat_obj = CatNormalResource(
                **cat_data
            )
            tmp_cat_normal_models.append(cat_obj)

        if len(tmp_cat_normal_models) >= 1000:
            yield tmp_cat_normal_models
            tmp_cat_normal_models = []

    yield tmp_cat_normal_models


@celery_app.task
def insert_normal_cat_data(data):
    """
    使用异步，每次用bulk 批量插入 1000条数据
    :param data:
    :return:
    """
    try:
        for i in add_normal_cat_data(data):
            CatNormalResource.objects.bulk_create(i)
    except Exception as e:
        print(e)
        raise RsError('插入数据库失败')


def add_cat_data(start_time, end_time):
    """
    真实的正常数据、判断的异常可能是正常，
    此时需人为主动插入数据
    :param start_time:
    :param end_time:
    :return:
    """
    data = get_cache_cat_data(start_time, end_time)
    tmp_cat_normal_models = []

    for cat_data in data:
        cat_data['id'] = str(uuid4())
        cat_obj = CatNormalResource(
            **cat_data
        )
        tmp_cat_normal_models.append(cat_obj)

        if len(tmp_cat_normal_models) >= 1000:
            yield tmp_cat_normal_models
            tmp_cat_normal_models = []

    yield tmp_cat_normal_models


@celery_app.task
def insert_cat_data(start_time, end_time):
    """
    使用异步,批量插入指定时间段的cat数据
    :param start_time:
    :param end_time:
    :return:
    """
    try:
        for i in add_cat_data(start_time, end_time):
            CatNormalResource.objects.bulk_create(i)
    except Exception as e:
        print(e)
        raise RsError('插入数据库失败')
