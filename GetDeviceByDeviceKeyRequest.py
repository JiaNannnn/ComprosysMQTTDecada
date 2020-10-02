from enosapi.request.EnOSRequest import EnOSRequest
from enosapi.util.const import Const

class GetDeviceByDeviceKeyRequest(EnOSRequest):
    """Retrieve information about a device based on its product and device key

    :param org_id: DECADA organisation unit (OU) id
    :type org_id: str

    :param product_key: product key id
    :type product_key: str

    :param device_key: device key id
    :type device_key: str

    :param params: optional parameters to be passed to request
    :type params: dict, optional
    """
    __url = '/connectService/products/{product_key}/devices/{device_key}'
    __type = Const.request_get
    __context_type = 'application/json'

    def __init__(self, org_id, product_key, device_key, params=None):
        self.org_id = org_id
        self.product_key = product_key
        self.device_key = device_key
        self.params = params

    def get_request_url(self):
        return self.__url.replace("{product_key}", self.product_key) \
            .replace("{device_key}", self.device_key)

    def get_request_type(self):
        return self.__type

    def get_content_type(self):
        return self.__context_type

    def get_params(self):
        return self.params
