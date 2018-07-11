import unittest
from datetime import datetime

from vl_logger import vlogfield
from vl_logger.vutils import VLogType


class TestFieldCreation(unittest.TestCase):

    def test_get_datetime(self):
        token = "2018-05-08 14:33:22.984875"
        datetime_field = vlogfield.Datetime(token)
        format = " ".join(["%Y-%m-%d", "%H:%M:%S.%f"])
        datetime_obj = datetime.strptime(token, format)
        self.assertEqual(datetime_field.get_datetime(), datetime_obj)

    def test_correct_tokens(self):
        dt_token = "2018-05-08 14:33:22.984875"
        type_token = VLogType.DEBUG
        source_token = "[res.core.absolute:636]"
        thread_token = "[MainProcess:MainThread]"
        details_token = "Sending HTTP POST request to server_url"

        datetime = vlogfield.Datetime(dt_token)
        self.assertEqual(str(datetime), "2018-05-08 14:33:22.984875")

        type = vlogfield.Type(type_token)
        self.assertEqual(type.get_type(), VLogType.DEBUG)
        self.assertEqual(str(type), "DEBUG")

        source = vlogfield.Source(source_token)
        self.assertEqual(str(source), source_token)
        self.assertEqual(source.get_module(), "res.core.absolute")
        self.assertEqual(source.get_line_number(), 636)

        thread = vlogfield.Thread(thread_token)
        self.assertEqual(str(thread), thread_token)
        self.assertEqual(thread.get_process(), "MainProcess")
        self.assertEqual(thread.get_thread(), "MainThread")

        details = vlogfield.Details(details_token)
        self.assertEqual(str(details), details_token)

    def test_api_formatting(self):
        api_request = """Sending HTTP POST request to server_url: """ \
                      """https://10.10.10.10:80/json-rpc/10.1; {"params": {"cluster": {"cluster": """ \
                      """"Cluster1"}, "force": false}, "method": "SetClusterConfig", "id": 8}."""
        api_response = """JSON-RPC-POST response: {"id": 8, "result": {"clusterInfo": {""" \
            """"repCount": 2, "encryptionAtRestState": "enabled", "attributes": {}, """ \
            """"ensemble": ["10.117.208.26", "10.117.208.41"], "NodeID": 3}}}"""

        display_request = """\n  JSON-RPC-POST request (id: 8)\n""" \
                          """    Method: SetClusterConfig\n""" \
                          """    URL: https://10.10.10.10:80/json-rpc/10.1\n""" \
                          """    Params: {u'cluster': {u'cluster': u'Cluster1'}, u'force': False}"""
        display_response = """\n  JSON-RPC-POST response (id: 8): Result\n""" \
                           """    {u'clusterInfo': {u'NodeID': 3,\n""" \
                           """                  u'attributes': {},\n""" \
                           """                  u'encryptionAtRestState': u'enabled',\n""" \
                           """                  u'ensemble': [u'10.117.208.26', u'10.117.208.41'],\n""" \
                           """                  u'repCount': 2}}"""
        request_log = vlogfield.Details(api_request)
        request_log.format_api_calls()
        self.assertEqual(str(request_log), display_request)
        response_log = vlogfield.Details(api_response)
        response_log.format_api_calls()
        self.assertEqual(str(response_log), display_response)

    def test_correct_traceback_tokens(self):
        step_token = '  File "/home/http_utils.py", line 1078, in _call_cluster_api\n' \
                     '    check_json_rpc_response(json_response, retry_faults, method)'
        exp_token = '''ApiCallMethodException: Error calling Method: ''' \
                    '''DoesNotExist. JSON response: {u'id': 63}'''
        step = vlogfield.TracebackStep(step_token)
        self.assertEqual(step.get_file(), "/home/http_utils.py")
        self.assertEqual(step.get_line_num(), 1078)
        self.assertEqual(step.get_function(), "_call_cluster_api")
        self.assertEqual(step.get_line(), "check_json_rpc_response(json_response, retry_faults, method)")
        self.assertEqual(str(step), step_token)

        exception = vlogfield.TracebackException(exp_token)
        self.assertEqual(str(exception), exp_token)
        self.assertEqual(exception.get_exception(), "ApiCallMethodException")
        self.assertEqual(exception.get_desc(), "Error calling Method: "
                                               "DoesNotExist. JSON response: {u'id': 63}")

    def test_incorrect_tokens(self):
        token = "Garbage"
        with self.assertRaises(ValueError):
            vlogfield.Datetime(token)
        with self.assertRaises(ValueError):
            vlogfield.Type("Garbage")
        with self.assertRaises(ValueError):
            vlogfield.Source("Garbage")
        with self.assertRaises(ValueError):
            vlogfield.Thread("Garbage")


if __name__ == '__main__':
    unittest.main()