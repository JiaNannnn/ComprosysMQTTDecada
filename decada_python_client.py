from enos.core.MqttClient import MqttClient
from enos.message.upstream.tsl.AttributeQueryRequest import AttributeQueryRequest
from enos.message.upstream.tsl.AttributeUpdateRequest import AttributeUpdateRequest
from enos.message.upstream.tsl.MeasurepointPostRequest import MeasurepointPostRequest
from enos.message.downstream.ota.OtaUpgradeCommand import OtaUpgradeCommand
from enos.message.upstream.ota.OtaGetVersionRequest import OtaGetVersionRequest
from enos.message.upstream.ota.OtaProgressReportRequest import OtaProgressReportRequest
from enos.message.upstream.ota.OtaVersionReportRequest import OtaVersionReportRequest
from enos.message.downstream.tsl.ServiceInvocationCommand import ServiceInvocationCommand
from enos.message.downstream.tsl.ServiceInvocationReply import ServiceInvocationReply

from enosapi.request.PostMeasurepointsEnOSRequest import PostMeasurepointsEnOSRequest
from enosapi.client.EnOSDefaultClient import EnOSDefaultClient

from enosapi.client.EnOSDefaultClient import EnOSDefaultClient
from enosapi.request.PostMeasurepointsEnOSRequest import PostMeasurepointsEnOSRequest

from GetDeviceByDeviceKeyRequest import GetDeviceByDeviceKeyRequest

from datetime import datetime
from hashlib import sha256
from zipfile import ZipFile
import json
import re
import os
import requests
import sys
import threading
import time
import yaml

# Wrapper class which makes it easier to communicate with Decada
#  The class is pretty straightforward to use:
#
#  To instantiate and connect
#  <code>
#  decadaPythonClient = DecadaPythonClient(baseDirectory, configPath, connectSuccessCallback, connectFailedCallback)
#  decadaPythonClient.connect()
#  </code>


class DecadaPythonClient:
    """Wrapper class which makes it easier to communicate with DECADA

    :param baseDirectory: provides the path to the directory of the config file
    :type baseDirectory: str

    :param configPath: config file name
    :type configPath: str

    :param onConnectSuccessCallback: method hook that is called upon connection success
    :type onConnectSuccessCallback: def, optional

    :param onConnectFailedCallback: method hook that is called upon connection failure
    :type onConnectFailedCallback: def, optional
    """

    def __init__(
            self,
            baseDirectoryPath,
            yamlFilePath,
            onConnectSuccessCallback=None,
            onConnectFailedCallback=None):

        self.__baseDirectoryPath = baseDirectoryPath
        self.__orgId = None
        self.__appAccessKey = None
        self.__appSecretKey = None
        self.__apiUrlV1 = None
        self.__apiUrlV2 = None
        self.__mqttUrl = None
        self.__productKey = None
        self.__deviceKey = None
        self.__deviceSecret = None
        self.__caFile = None
        self.__keyFile = None
        self.__cerFile = None
        self.__keyFilePassword = None

        self.__mqttClient = None
        self.__postClient = None
        self.__serviceInvocationHandlers = {}
        self.__restartHandler = None
        self.__assetId = None

        self.__filePathPattern = re.compile(r"((?:[\w]\:)?\/{1,2}.*?\.[\w]+)")

        self.__externalConnectSuccessCallback = onConnectSuccessCallback
        self.__externalConnectFailedCallback = onConnectFailedCallback

        try:
            configFile = open(baseDirectoryPath + "/" + yamlFilePath, "rb")
        except IOError:
            print('Unable to open configuration file: ' +
                  baseDirectoryPath + "/" + yamlFilePath)
            sys.exit()

        with configFile:
            documents = yaml.full_load(configFile)
            decadaConfig = documents.get("decada")

            if (decadaConfig is not None):
                self.__orgId = decadaConfig.get("orgId")
                self.__appAccessKey = decadaConfig.get("appAccessKey")
                self.__appSecretKey = decadaConfig.get("appSecretKey")
                self.__apiUrlV1 = decadaConfig.get("apiUrlV1")
                self.__apiUrlV2 = decadaConfig.get("apiUrlV2")
                self.__mqttUrl = decadaConfig.get("mqttUrl")
                self.__productKey = decadaConfig.get("productKey")
                self.__deviceKey = decadaConfig.get("deviceKey")
                self.__deviceSecret = decadaConfig.get("deviceSecret")
                self.__caFile = baseDirectoryPath + \
                    "/" + decadaConfig.get("caFile")
                self.__keyFile = baseDirectoryPath + \
                    "/" + decadaConfig.get("keyFile")
                self.__cerFile = baseDirectoryPath + \
                    "/" + decadaConfig.get("cerFile")
                self.__keyFilePassword = decadaConfig.get("keyFilePassword")

        if (self.__mqttUrl is not None and self.__productKey is not None and self.__deviceKey is not None and
            self.__deviceSecret is not None and self.__caFile is not None and self.__keyFile is not None and
            self.__cerFile is not None and self.__keyFilePassword is not None and self.__orgId is not None and
            self.__appAccessKey is not None and self.__appSecretKey is not None and
                self.__apiUrlV1 is not None and self.__apiUrlV2 is not None):

            print(self.__orgId)
            print(self.__appAccessKey)
            print(self.__appSecretKey)
            print(self.__apiUrlV1)
            print(self.__apiUrlV2)
            print(self.__mqttUrl)
            print(self.__productKey)
            print(self.__deviceKey)
            print(self.__deviceSecret)
            print(self.__caFile)
            print(self.__keyFile)
            print(self.__cerFile)
            print(self.__keyFilePassword)

    # Internal method for setting up a MqttClient
    #   @param self The object pointer
    def __setupMqttClient(self):
        self.__mqttClient = MqttClient(
            self.__mqttUrl,
            self.__productKey,
            self.__deviceKey,
            self.__deviceSecret)
        self.__mqttClient.get_profile().set_auto_reconnect(True)

        if (os.path.isfile(self.__caFile) and os.path.isfile(
                self.__keyFile) and os.path.isfile(self.__cerFile)):
            self.__mqttClient.get_profile().set_ssl_context(
                self.__caFile,
                self.__cerFile,
                self.__keyFile,
                self.__keyFilePassword)

        self.__mqttClient.onOnline = self.__onOnline
        self.__mqttClient.onOffline = self.__onOffline
        self.__mqttClient.onConnectFailed = self.__onConnectFailed
        self.__mqttClient.on_disconnect = self.__onDisconnect

        self.__mqttClient.connect()

    # Internal callback method when client connects to decada
    #   @param self The Object pointer
    def __onOnline(self):
        print("Connected with Decada")

        request = GetDeviceByDeviceKeyRequest(
            org_id=self.__orgId,
            product_key=self.__productKey,
            device_key=self.__deviceKey)

        response = self.__postClient.execute(request)
        if response.status == 0 and "assetId" in response.data:
            self.__assetId = response.data["assetId"]
            print(self.__assetId)

        if self.__externalConnectSuccessCallback is not None:
            self.__externalConnectSuccessCallback()

    # Internal callback method on client disconnects from decada
    #   @param self The Object pointer
    def __onOffline(self):
        print("Disconnected with Decada")

    # Internal callback method when client connection with decada failed
    def __onConnectFailed(self):
        print("Connection with Decada failed")
        if self.__externalConnectFailedCallback is not None:
            self.__externalConnectFailedCallback()

    def __onDisconnect(self):
        print("On Disconnect from Decada")

    # Internal method which generates the neccesary hash to make an api call to decada
    #   @param url
    def __generateUrl(self, url,sign):

        params = {"path": url}
        timeStamp = str(int(time.time() * 1000))
        params["requestTimestamp"] = timeStamp
        params["orgId"] = self.__orgId

        signStr = self.__appAccessKey
        keys = sorted(params.keys())

        for key in keys:
            signStr += key + str(params[key])

        signStr += self.__appSecretKey
        psw = sha256()
        psw.update(signStr.encode('utf8'))
        sign = psw.hexdigest().upper()
        apiUrl = "{}/sys/productkey={}/integration/measurepoint/post"\
        .format(self.__apiUrlV2,url,self.__productKey)
        #apiUrl = "{}/commonFileService/files?path={}&accessKey={}&requestTimestamp={}&sign={}&orgId={}" \
            #.format(self.__apiUrlV1, url, self.__appAccessKey, timeStamp, sign, self.__orgId)

        return apiUrl

    # Public method which starts the connecting process to decada
    #   @param self

    def connect(self):
        """Starts the connection process to DECADA
        """
        self.__postClient = EnOSDefaultClient(
            self.__apiUrlV1, self.__appAccessKey, self.__appSecretKey)
        self.__setupMqttClient()

    def postMeasurePoints(self, measurePointsDict):
        """Posts measure points to DECADA

        :param measurePointsDict: Python dict containing measurepoints in key-value pair format
        :type measurePointsDict: dict
        """
        print("posting measurepoints")

        filesToUpload = {}
        index = 0

        for key, value in measurePointsDict.items():
            if isinstance(value, dict):
                for subKey, subValue in value.items():

                    match = self.__filePathPattern.match(str(subValue))
                    if match is not None:
                        filePath = match.group(1)
                        name = "file" + str(index)
                        index = index + 1

                        value[subKey] = "local://" + name
                        filesToUpload[name] = open(filePath, "rb")

            else:
                match = self.__filePathPattern.match(str(value))
                if match is not None:
                    filePath = match.group(1)
                    name = "file" + str(index)
                    index = index + 1

                    measurePointsDict[key] = "local://" + name
                    filesToUpload[name] = open(filePath, "rb")

        if index == 0:  # no binary file as values
            measurePointRequestBuilder = MeasurepointPostRequest.builder() \
                .set_product_key(self.__productKey) \
                .set_device_key(self.__deviceKey)

            measurePointRequestBuilder = measurePointRequestBuilder.add_measurepoints(
                measurePointsDict)
            measurePointRequest = measurePointRequestBuilder.set_timestamp(
                int(time.time() * 1000)) .build()

            measurePointResponse = self.__mqttClient.publish(
                measurePointRequest)
            if measurePointRequest:
                print(
                    'MeasurePointPostResponse: {}'.format(
                        measurePointResponse.get_code()))

        else:
            data = [{
                "measurepoints": measurePointsDict,
                "assetId": self.__assetId,
                "time": time.time() * 1000
            }]

            params = {
                "data": json.dumps(data)
            }

            request = PostMeasurepointsEnOSRequest(
                org_id=self.__orgId,
                product_key=self.__productKey,
                params=params,
                upload_file=filesToUpload)

            response = self.__postClient.execute(request)
            print("PostMeasurepointsEnOSRequest: {}, {}, {}".format(
                response.status, response.msg, response.data))

    def queryAttributes(self, keys):
        """Query attributes of asset from DECADA

        :param keys: Python dict containing measurepoints in key-value pair format
        :type keys: list
        :return: dictionary containing the value to each queried field
        :rtype: dict
        """
        attributeQueryRequestBuilder = AttributeQueryRequest.builder()

        if (len(keys) > 0):
            for i in keys:
                attributeQueryRequestBuilder = attributeQueryRequestBuilder \
                    .add_attribute(i)
        else:
            attributeQueryRequestBuilder = attributeQueryRequestBuilder.query_all()

        attributeQueryRequest = attributeQueryRequestBuilder.build()
        attributeQueryResponse = self.__mqttClient.publish(
            attributeQueryRequest)
        if attributeQueryResponse.get_code() == 200:
            return json.loads(attributeQueryResponse.get_data())
        return None

    # Public method which allow callers to update attributes
    #   @param self
    #   @param attributesDict Dictionary containing key-value pairs of attributes to be updated
    def updateAttributes(self, attributesDict):
        """Update attributes of asset

        :param attributesDict: Python dict containing attributes in key-value pair format
        :type attributesDict: dict
        """
        attributeUpdateRequestBuilder = AttributeUpdateRequest.builder() \
            .set_product_key(self.__productKey) \
            .set_device_key(self.__deviceKey)

        for key, value in attributesDict.items():
            attributeUpdateRequestBuilder = attributeUpdateRequestBuilder.add_attribute(
                key, value)

        attributeUpdateRequest = attributeUpdateRequestBuilder.build()
        attributeUpdateResponse = self.__mqttClient.publish(
            attributeUpdateRequest)
        if attributeUpdateResponse:
            print("AttributeUpdateResponse: {}".format(
                attributeUpdateResponse.get_code()))
def print1(self,sign):
        params = {"path": url}
        timeStamp = str(int(time.time() * 1000))
        params["requestTimestamp"] = timeStamp
        params["orgId"] = self.__orgId

        signStr = self.__appAccessKey
        keys = sorted(params.keys())

        for key in keys:
            signStr += key + str(params[key])

        signStr += self.__appSecretKey
        psw = sha256()
        psw.update(signStr.encode('utf8'))
        sign = psw.hexdigest().upper()
        print("1")
        print(sign)
        return sign

#def post_payload(client,payload_dict):

decada_client = DecadaPythonClient(os.getcwd(), "/config.yaml")
decada_client.connect()

time.sleep(1)

#client.postMeasurePoints(payload_dict)

#print(client.queryAttributes(["id"]))

#client.updateAttributes({"id": 100})

#print(client.queryAttributes(["id"]))