import pytest
import requests


class ApiClient:
    """
    统一管理URL请求
    """
    def __init__(self,base_url:str,timeout:int=5,token:str|None=None)->None:
        """
        初始化
        :param base_url: 基础URL
        :param timeout: 超时时间
        :param token: 令牌token
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session() #建立会话
        if token:
            #向请求头添加token
            self.session.headers.update({"Authorization":f"Bearer {token}"})

    def _request(self,modest:str,end_url:str,**kwargs)->requests.Response:
        """
        进行发送网络请求
        :param modest:请求模式（例如：get,post,put,patch,delete）
        :param end_url:末尾URL地址
        :param kwargs:发送数据
        :return: 请求后收到的response对象
        """
        url = self.base_url + end_url
        kwargs.setdefault("timeout",self.timeout)
        response = self.session.request(modest,url,**kwargs)
        try:
            response.json_data = response.json()
        except ValueError:
            response.json_data = None
        return response

    def get(self,end_url:str,params:dict|None=None,headers:dict|None=None)->requests.Response:
        """
        get请求调用接口
        :param end_url: 末尾URL地址
        :param params:  get请求携带数据
        :param headers: 请求头数据
        :return:请求后收到的response对象
        """
        return self._request("get",end_url,params=params,headers=headers)

    def post(self,end_url:str,data:dict|None=None,json:dict|None=None,headers:dict|None=None)->requests.Response:
        """
        post请求调用接口
        :param end_url: 末尾URL地址
        :param data: data格式请求体
        :param json: json格式请求体
        :param headers: 额外请求头数据
        :return: 请求后收到的response对象
        """
        return self._request("post",end_url,data=data,json=json,headers=headers)


    def head(self,end_url:str,headers:dict|None=None) -> requests.Response:
        """
        head请求调用接口
        :param end_url: 末尾URL地址
        :param headers: 额外请求头数据
        :return: 请求后收到的response对象
        """
        return self._request("head",end_url,headers=headers)


@pytest.fixture
def client()->ApiClient:
    """
    根据根地址返回URL接口类
    :return: ApiClient类
    """
    url = "http://127.0.0.1:8000"
    return ApiClient(url)

def test_get(client:ApiClient)->None:
    """
    测试get请求
    """
    response = client.get("/")
    assert response.status_code == 200
    pass

def test_post(client:ApiClient)->None:
    """
    测试post请求
    """
    json={}
    response = client.post("/",json=json)
    assert response.status_code == 200
    pass

def test_head(client:ApiClient)->None:
    """
    测试head请求
    """
    response = client.head("/")
    assert response.status_code == 200
    pass

@pytest.mark.parametrize("user_id",[1,2,3])
def test_gets(client:ApiClient,user_id:int)->None:
    """多项测试"""
    response = client.get(f"/users/{str(user_id)}")
    assert response.status_code == 200
    pass