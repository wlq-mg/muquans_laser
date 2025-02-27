import requests
import time

    
class ApiError(Exception):

    def __init__(self, message):
        self.message = message

class RestClient:

    def __init__(self, base_url : str, insecure_certifiate=False, verbose=False):
        self.base_url = base_url
        self.session = requests.Session()
        self.verbose = verbose
        
        if insecure_certifiate:
            # disable certificate verify and warning
            self.session.verify = False
            from urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def get(self, endpoint : str):
        url = f"{self.base_url}/{endpoint}"
        if self.verbose:
            print(f'get:{url}')
        response = self.session.get(url)
        self.raise_on_error(response)
        return response.json()

    def post(self, endpoint : str, data, skip_response=False):
        url = f"{self.base_url}/{endpoint}"
        if self.verbose:
            print(f'post:{url} payload:{data}')
        response = self.session.post(url, json=data)
        self.raise_on_error(response)
        if not skip_response:
            return response.json() if response.text else None
        return None

    def put(self, endpoint : str, data):
        url = f"{self.base_url}/{endpoint}"
        if self.verbose:
            print(f'put:{url} payload:{data}')
        response = self.session.put(url, json=data)
        self.raise_on_error(response)
        return response.json() if response.text else None

    def delete(self, endpoint : str):
        url = f"{self.base_url}/{endpoint}"
        if self.verbose:
            print(f'delete:{url}')
        response = self.session.delete(url)
        self.raise_on_error(response)
        return response.json() if response.text else None
    
    def raise_on_error(self, response: requests.Session):
        if not response.ok:
            raise ApiError(f'Error {response.status_code} for {response.url}. {response.text}')

class ApiV1(RestClient):

    def __init__(self, host : str, verbose=False):
        RestClient.__init__(self, f"https://{host}/api/v1", insecure_certifiate=True)
        self.verbose = verbose

    def auth(self, login : str, password : str):
        self.post("/auth/login", {"login": login, "password": password})

    # return dict of all monit roles
    def sys_monit_roles(self):
        return self.get("/system/monitoring/roles")

    # return dict of all monit values
    def sys_monit_values(self):
        arr = self.get("/system/monitoring/values")
        return dict(map(lambda e: (e["id"], e["val"]), arr))

    # return dict of all actions roles
    def sys_actions_roles(self):
        return self.get("/system/actions/roles")

    # return job uuid if wait_complete == False
    def sys_action_run(self, gid : str, aid : str, state=None, wait_complete=False):
        uuid = self.post(
            "/system/actions/job", 
            {
                "gid": gid, 
                "aid": aid, 
                "state": state
            }
        )["id"]
        return self.sys_action_wait_complete(uuid) if wait_complete else uuid

    def sys_action_feedback(self, uuid : str):
        return self.get(f"/system/actions/job/{uuid}")

    def sys_action_wait_complete(self, uuid : str):
        while True:
            feedback = self.sys_action_feedback(uuid)
            if self.verbose:
                print(feedback)
            if feedback["error"] == True:
                raise ApiError(f'action failed with error : {feedback["message"]}')
            if feedback["state"] == "FINISHED":
                break
            time.sleep(1.0)

    # return dict of all actions roles
    def seq_roles(self):
        return self.get("/sequencer/roles")
        
    def seq_run(self, sequence, aliases = {}, triggered = False, loop_count = 1, wait_complete=False):
        self.post("/sequencer/sequence", 
                  sequence, 
                  skip_response=True)
        self.post("/sequencer/aliases", 
                  aliases, 
                  skip_response=True)
        self.post("/sequencer/run", 
                  {
                      "triggered": triggered,
                      "loopCount": loop_count
                  }, 
                  skip_response=True)
        if wait_complete:
            self.seq_wait_complete()
        
    def seq_feedback(self):
        return self.get(f"/sequencer/status")

    def seq_wait_complete(self):
        while True:
            feedback = self.seq_feedback()
            if self.verbose:
                print(feedback)
            if feedback["error"] == True:
                raise ApiError(f'action failed with error : {feedback["message"]}')
            if not feedback["running"]:
                break
            time.sleep(1.0)