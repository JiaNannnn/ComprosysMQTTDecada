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

